"""
Pydantic schemas for source management.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SourceBase(BaseModel):
    """Base source schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    source_type: str = Field(..., regex="^(book|article|document|letter|speech|manuscript|other)$")
    author: Optional[str] = Field(None, max_length=200)
    publication_date: Optional[datetime] = None
    publisher: Optional[str] = Field(None, max_length=200)
    isbn: Optional[str] = Field(None, max_length=20)
    url: Optional[str] = Field(None, max_length=500)
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return []
        # Ensure all tags are strings and not empty
        return [tag.strip() for tag in v if tag and tag.strip()]

    @validator('url')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SourceCreate(SourceBase):
    """Schema for creating a source."""
    pass


class SourceUpdate(BaseModel):
    """Schema for updating a source."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    source_type: Optional[str] = Field(None, regex="^(book|article|document|letter|speech|manuscript|other)$")
    author: Optional[str] = Field(None, max_length=200)
    publication_date: Optional[datetime] = None
    publisher: Optional[str] = Field(None, max_length=200)
    isbn: Optional[str] = Field(None, max_length=20)
    url: Optional[str] = Field(None, max_length=500)
    reliability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return None
        return [tag.strip() for tag in v if tag and tag.strip()]

    @validator('url')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SourceResponse(SourceBase):
    """Schema for source responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    document_count: int = 0
    total_chunks: int = 0

    class Config:
        from_attributes = True


class SourceSummary(BaseModel):
    """Summary schema for source listings."""
    id: UUID
    title: str
    source_type: str
    author: Optional[str]
    reliability_score: float
    document_count: int
    total_chunks: int
    created_at: datetime
    tags: List[str]

    class Config:
        from_attributes = True