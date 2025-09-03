"""
Chunk model for document text chunks with embeddings.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from database import Base


class Chunk(Base):
    """Chunk model for document text chunks with vector embeddings."""
    
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=True)
    
    # Metadata
    word_count = Column(Integer, nullable=False)
    char_count = Column(Integer, nullable=False)
    
    # Foreign keys
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
    
    @property
    def source_title(self):
        """Get source title through document relationship."""
        return self.document.source.title if self.document and self.document.source else None
    
    @property
    def trust_tier(self):
        """Get trust tier through document relationship."""
        return self.document.source.trust_tier if self.document and self.document.source else None