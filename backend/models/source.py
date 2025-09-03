"""
Source model for document sources.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Source(Base):
    """Source model for historical documents and references."""
    
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    type = Column(String(100), nullable=False)  # book, letter, speech, newspaper, etc.
    provenance_url = Column(Text, nullable=True)
    license = Column(String(100), nullable=True)
    trust_tier = Column(Integer, nullable=False)  # 1=primary, 2=peer-reviewed, 3=reference, 4=other
    notes = Column(Text, nullable=True)
    sha256 = Column(String(64), unique=True, nullable=True)
    
    # Foreign keys
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<Source(id={self.id}, title={self.title}, trust_tier={self.trust_tier})>"