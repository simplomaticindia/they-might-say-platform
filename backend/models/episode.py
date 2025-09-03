"""
Episode model for conversation sessions.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Episode(Base):
    """Episode model for conversation sessions."""
    
    __tablename__ = "episodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")  # draft, recording, completed, archived
    
    # Episode metadata
    total_beats = Column(Integer, default=0, nullable=False)
    total_duration = Column(Integer, nullable=True)  # in seconds
    
    # Foreign keys
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    persona_pack_id = Column(UUID(as_uuid=True), ForeignKey("persona_packs.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    host = relationship("User", foreign_keys=[host_id])
    persona_pack = relationship("PersonaPack")
    beats = relationship("Beat", back_populates="episode", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="episode")
    
    def __repr__(self):
        return f"<Episode(id={self.id}, title={self.title}, status={self.status})>"
    
    @property
    def beat_count(self):
        """Get current number of beats in episode."""
        return len(self.beats) if self.beats else 0
    
    def to_dict(self):
        """Convert episode to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "total_beats": self.total_beats,
            "total_duration": self.total_duration,
            "host_id": str(self.host_id),
            "persona_pack_id": str(self.persona_pack_id) if self.persona_pack_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }