from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"  # "admin" or "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    title: str
    author: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    file_path: str
    index_status: str
    visibility: str
    uploaded_at: datetime
    uploaded_by: int

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None

# Chat Schemas
class CitationItem(BaseModel):
    page: int
    source: str
    snippet: Optional[str] = None

class ChatMessageCreate(BaseModel):
    question: str
    session_id: Optional[int] = None

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: Optional[List[CitationItem]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    created_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True

# Summary Schemas
class SummaryResponse(BaseModel):
    document_id: int
    summary: str
    generated_at: datetime
    cached: bool = True

    class Config:
        from_attributes = True

# Stats
class SystemStats(BaseModel):
    total_documents: int
    public_documents: int
    personal_documents: int
    total_users: int
