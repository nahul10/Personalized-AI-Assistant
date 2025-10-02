# backend/schemas.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from .state import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    # Legacy support columns
    name = Column(String, nullable=True)             # old NOT NULL in some DBs
    filename = Column(String, nullable=True)         # preferred going forward
    source_path = Column(String, nullable=True)
    file_type  = Column(String, nullable=True)       # pdf, docx, txt, image
    pages = Column(Integer, default=0)
    chunks = Column(Integer, default=0)
    ocr_pages = Column(Integer, default=0)           # ✅ how many pages needed OCR
    uploaded_at = Column(DateTime, default=datetime.utcnow)  # legacy
    created_at  = Column(DateTime, default=datetime.utcnow)

    chunks_rel = relationship("Chunk", back_populates="file", cascade="all,delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), index=True, nullable=False)
    page_no = Column(Integer, default=0)
    seq_no = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    emb_dim = Column(Integer, default=0)
    embedding = Column(LargeBinary, nullable=True)   # np.float32 bytes
    file = relationship("File", back_populates="chunks_rel")

class QAHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    mode = Column(String, default="RAG")             # RAG | SQL | TRANSLATE
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
