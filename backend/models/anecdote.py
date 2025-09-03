"""
Anecdote model for curated historical stories.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Anecdote(Base):
    """Anecdote model for curated historical stories and facts."""
    
    __tablename__ = "anecdotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True)  # personal, political, wartime, etc.
    tags = Column(String(500), nullable=True)  # comma-separated tags
    
    # Verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(Text, nullable=True)
    trust_level = Column(Integer, default=3, nullable=False)  # 1-5 scale
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    primary_source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    primary_source = relationship("Source", foreign_keys=[primary_source_id])
    creator = relationship("User", foreign_keys=[created_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<Anecdote(id={self.id}, title={self.title}, verified={self.is_verified})>"
    
    def to_dict(self):
        """Convert anecdote to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "category": self.category,
            "tags": self.tags.split(",") if self.tags else [],
            "is_verified": self.is_verified,
            "verification_notes": self.verification_notes,
            "trust_level": self.trust_level,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "primary_source_id": str(self.primary_source_id) if self.primary_source_id else None,
            "created_by": str(self.created_by),
            "verified_by": str(self.verified_by) if self.verified_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }