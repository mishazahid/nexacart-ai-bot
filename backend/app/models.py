"""
NexaCart AI Support Bot - SQLAlchemy ORM Models

Defines database tables for chat logs and document chunks.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class ChatLog(Base):
    """Stores each chat interaction for analytics and audit purposes."""

    __tablename__ = "chat_logs"

    id: str = Column(Text, primary_key=True, default=_generate_uuid)
    session_id: str = Column(Text, nullable=False, index=True)
    query: str = Column(Text, nullable=False)
    response: str = Column(Text, nullable=False)
    confidence_score: float = Column(Float, nullable=False, default=0.0)
    sources: str = Column(Text, nullable=True)  # JSON-serialised list of source dicts
    is_fallback: bool = Column(Boolean, nullable=False, default=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<ChatLog id={self.id!r} session={self.session_id!r} "
            f"confidence={self.confidence_score:.2f} fallback={self.is_fallback}>"
        )


class DocumentChunk(Base):
    """Stores metadata for every document chunk ingested into the knowledge base."""

    __tablename__ = "document_chunks"

    id: str = Column(Text, primary_key=True, default=_generate_uuid)
    filename: str = Column(Text, nullable=False, index=True)
    chunk_index: int = Column(Integer, nullable=False)
    content: str = Column(Text, nullable=False)
    word_count: int = Column(Integer, nullable=False, default=0)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk id={self.id!r} file={self.filename!r} "
            f"chunk={self.chunk_index} words={self.word_count}>"
        )
