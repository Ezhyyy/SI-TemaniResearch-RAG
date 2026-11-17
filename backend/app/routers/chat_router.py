import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, ChatSession, ChatMessage, User
from app.schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionResponse,
    CitationItem
)
from app.auth import get_current_user
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

def parse_citations(citations_str: Optional[str]) -> Optional[List[CitationItem]]:
    if not citations_str:
        return None
    try:
        data = json.loads(citations_str)
        return [CitationItem(**item) for item in data]
    except Exception:
        return None

@router.post("/{document_id}", response_model=ChatMessageResponse)
def send_chat_message(
    document_id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validasi keberadaan dokumen
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan")

    if doc.visibility == "private" and doc.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak ke dokumen privat")

    if doc.index_status != "Ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dokumen sedang dalam status '{doc.index_status}'. Tunggu sampai proses indexing selesai."
        )

    # 2. Dapatkan atau buat Chat Session
    session = None
    if payload.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == payload.session_id,
            ChatSession.user_id == current_user.id
        ).first()

    if not session:
        session = ChatSession(
            user_id=current_user.id,
            document_id=document_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 3. Simpan pesan user
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.question
    )
    db.add(user_msg)
    db.commit()

    # 4. Ambil history percakapan sebelumnya
    prev_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    history = [{"role": m.role, "content": m.content} for m in prev_messages]

    # 5. Eksekusi RAG Q&A
    answer_text, citations_list = rag_service.answer_question(
        document_id=doc.id,
        document_title=doc.title,
        question=payload.question,
        history=history
    )

    # 6. Simpan pesan asisten & sitasi
    citations_json = json.dumps(citations_list) if citations_list else None
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        citations=citations_json
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageResponse(
        id=assistant_msg.id,
        session_id=session.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        citations=parse_citations(assistant_msg.citations),
        created_at=assistant_msg.created_at
    )

@router.get("/{document_id}/sessions", response_model=List[ChatSessionResponse])
def get_user_document_sessions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.document_id == document_id,
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()

    response = []
    for s in sessions:
        msgs = [
            ChatMessageResponse(
                id=m.id,
                session_id=s.id,
                role=m.role,
                content=m.content,
                citations=parse_citations(m.citations),
                created_at=m.created_at
            )
            for m in s.messages
        ]
        response.append(ChatSessionResponse(
            id=s.id,
            user_id=s.user_id,
            document_id=s.document_id,
            created_at=s.created_at,
            messages=msgs
        ))
    return response

@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi chat tidak ditemukan")

    db.delete(session)
    db.commit()
    return {"message": "Sesi chat berhasil dihapus"}
