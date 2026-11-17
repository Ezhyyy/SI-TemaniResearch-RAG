from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, User
from app.schemas import SystemStats
from app.auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["Statistics"])

@router.get("", response_model=SystemStats)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_docs = db.query(Document).count()
    public_docs = db.query(Document).filter(Document.visibility == "public").count()
    personal_docs = db.query(Document).filter(Document.visibility == "private").count()
    total_users = db.query(User).count()

    return SystemStats(
        total_documents=total_docs,
        public_documents=public_docs,
        personal_documents=personal_docs,
        total_users=total_users
    )
