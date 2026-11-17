import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import Document, User, DocumentSummary
from app.schemas import DocumentResponse, DocumentUpdate, SummaryResponse
from app.auth import get_current_user
from app.services.rag_service import rag_service
from app.services.vector_service import vector_service

router = APIRouter(prefix="/api/documents", tags=["Documents"])

def run_indexing_task(document_id: int, file_path: str, db_session_maker):
    """Fungsi background task untuk memproses dan mengindeks PDF ke ChromaDB"""
    db = db_session_maker()
    try:
        success = rag_service.process_and_index_document(document_id, file_path)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.index_status = "Ready" if success else "Failed"
            db.commit()
    except Exception as e:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.index_status = "Failed"
            db.commit()
    finally:
        db.close()

@router.get("", response_model=List[DocumentResponse])
def get_documents(
    search: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
    visibility: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    query = db.query(Document)

    # Filter kepemilikan / visibilitas:
    # Dokumen publik bisa dilihat semua orang.
    # Dokumen privat hanya bisa dilihat oleh pemiliknya sendiri (user yang login).
    if current_user.role == "admin":
        # Admin bisa melihat semua dokumen
        pass
    else:
        query = query.filter(
            (Document.visibility == "public") | 
            ((Document.visibility == "private") & (Document.uploaded_by == current_user.id))
        )

    if visibility:
        query = query.filter(Document.visibility == visibility)
    if category:
        query = query.filter(Document.category == category)
    if year:
        query = query.filter(Document.year == year)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Document.title.ilike(search_pattern)) | 
            (Document.author.ilike(search_pattern))
        )

    return query.order_by(Document.uploaded_at.desc()).all()

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    author: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    visibility: Optional[str] = Form("public"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validasi file
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya file berekstensi .pdf yang diperbolehkan"
        )

    # Validasi hak visibilitas: user biasa hanya boleh upload sebagai "private" jika diinginkan
    doc_visibility = visibility
    if current_user.role != "admin" and visibility == "public":
        # Jika bukan admin tapi coba upload public, default ke private
        doc_visibility = "private"

    # Simpan file ke direktori uploads
    import uuid
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Buat record dokumen di DB dengan status 'Processing'
    doc = Document(
        title=title,
        author=author,
        year=year,
        category=category,
        description=description,
        file_path=file_path,
        index_status="Processing",
        visibility=doc_visibility,
        uploaded_by=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Jalankan proses indexing di background
    from app.database import SessionLocal
    background_tasks.add_task(run_indexing_task, doc.id, file_path, SessionLocal)

    return doc

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan")

    # Cek hak akses dokumen private
    if doc.visibility == "private" and doc.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda tidak memiliki akses ke dokumen ini")

    return doc

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan")

    if doc.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tidak berhak mengedit dokumen ini")

    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(doc, field, val)

    db.commit()
    db.refresh(doc)
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan")

    if doc.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tidak berhak menghapus dokumen ini")

    # 1. Hapus dari ChromaDB (atomik agar tidak ada ghost chunks)
    vector_service.delete_document_chunks(document_id)

    # 2. Hapus file fisik jika ada
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 3. Hapus dari database
    db.delete(doc)
    db.commit()

    return {"message": f"Dokumen '{doc.title}' dan indeks vektornya berhasil dihapus"}

@router.get("/{document_id}/summary", response_model=SummaryResponse)
def get_or_generate_summary(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan")

    # Cek cache ringkasan
    summary_record = db.query(DocumentSummary).filter(DocumentSummary.document_id == document_id).first()
    if summary_record:
        return SummaryResponse(
            document_id=document_id,
            summary=summary_record.summary,
            generated_at=summary_record.generated_at,
            cached=True
        )

    # Jika belum ada di cache, generate menggunakan Gemini
    summary_text = rag_service.generate_summary(doc.id, doc.title)

    # Simpan ke cache database
    new_summary = DocumentSummary(
        document_id=doc.id,
        summary=summary_text
    )
    db.add(new_summary)
    db.commit()
    db.refresh(new_summary)

    return SummaryResponse(
        document_id=doc.id,
        summary=new_summary.summary,
        generated_at=new_summary.generated_at,
        cached=False
    )
