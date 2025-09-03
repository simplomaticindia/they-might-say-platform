"""
Pydantic schemas for document management.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentResponse(DocumentBase):
    """Schema for document responses."""
    id: UUID
    source_id: UUID
    file_size: int
    file_hash: str
    word_count: int
    character_count: int
    chunk_count: Optional[int] = 0
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    """Summary schema for document listings."""
    id: UUID
    filename: str
    file_size: int
    word_count: int
    chunk_count: Optional[int] = 0
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True