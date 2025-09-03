"""
Citation model for linking responses to source chunks.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Citation(Base):
    """Citation model for linking AI responses to source chunks."""
    
    __tablename__ = "citations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_text = Column(Text, nullable=False)  # The AI response that includes this citation
    citation_text = Column(Text, nullable=False)  # The specific text being cited
    relevance_score = Column(Float, nullable=True)  # Relevance score from vector search
    page_anchor = Column(String(100), nullable=True)  # Page reference for citation
    
    # Foreign keys
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=True)
    beat_id = Column(UUID(as_uuid=True), ForeignKey("beats.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    chunk = relationship("Chunk", back_populates="citations")
    episode = relationship("Episode", back_populates="citations")
    beat = relationship("Beat", back_populates="citations")
    
    def __repr__(self):
        return f"<Citation(id={self.id}, chunk_id={self.chunk_id}, relevance_score={self.relevance_score})>"
    
    @property
    def source_info(self):
        """Get source information through chunk relationship."""
        if self.chunk and self.chunk.document and self.chunk.document.source:
            source = self.chunk.document.source
            return {
                "title": source.title,
                "author": source.author,
                "year": source.year,
                "trust_tier": source.trust_tier,
                "page": self.chunk.page_number,
            }
        return None