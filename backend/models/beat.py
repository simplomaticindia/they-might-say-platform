"""
Beat model for conversation segments.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Beat(Base):
    """Beat model for conversation segments within episodes."""
    
    __tablename__ = "beats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_number = Column(Integer, nullable=False)
    
    # Beat content
    host_prompt = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # Beat metadata
    response_time = Column(Float, nullable=True)  # Response generation time in seconds
    token_count = Column(Integer, nullable=True)  # Token count for the response
    citation_count = Column(Integer, default=0, nullable=False)
    
    # Beat status
    is_pinned = Column(String(50), default="unpinned", nullable=False)  # unpinned, pinned, saved
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    episode = relationship("Episode", back_populates="beats")
    creator = relationship("User", foreign_keys=[created_by])
    citations = relationship("Citation", back_populates="beat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Beat(id={self.id}, episode_id={self.episode_id}, sequence={self.sequence_number})>"
    
    def to_dict(self):
        """Convert beat to dictionary."""
        return {
            "id": str(self.id),
            "sequence_number": self.sequence_number,
            "host_prompt": self.host_prompt,
            "ai_response": self.ai_response,
            "response_time": self.response_time,
            "token_count": self.token_count,
            "citation_count": self.citation_count,
            "is_pinned": self.is_pinned,
            "notes": self.notes,
            "episode_id": str(self.episode_id),
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "citations": [citation.source_info for citation in self.citations] if self.citations else []
        }