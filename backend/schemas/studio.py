"""
Pydantic schemas for Studio Mode API.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationRequest(BaseModel):
    """Request schema for conversation generation."""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    source_ids: Optional[List[str]] = None
    episode_id: Optional[str] = None
    sequence_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CitationResponse(BaseModel):
    """Response schema for citations."""
    id: Optional[UUID] = None
    citation_text: str
    source_title: str
    source_author: Optional[str] = None
    confidence_score: float
    validation_score: Optional[float] = None
    context_snippet: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response schema for conversation generation."""
    response: str
    citations: List[Dict[str, Any]]
    beat_id: Optional[str] = None
    metadata: Dict[str, Any]


class EpisodeCreate(BaseModel):
    """Schema for creating an episode."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    persona_pack_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EpisodeUpdate(BaseModel):
    """Schema for updating an episode."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, regex="^(active|paused|completed|archived)$")
    metadata: Optional[Dict[str, Any]] = None


class EpisodeResponse(BaseModel):
    """Response schema for episodes."""
    id: UUID
    title: str
    description: Optional[str]
    persona_pack_id: Optional[UUID]
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    beat_count: int = 0
    total_citations: int = 0
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class BeatResponse(BaseModel):
    """Response schema for conversation beats."""
    id: UUID
    episode_id: UUID
    sequence_number: int
    user_message: str
    lincoln_response: str
    citations: List[Dict[str, Any]]
    created_at: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class EpisodeSummary(BaseModel):
    """Summary schema for episode listings."""
    id: UUID
    title: str
    status: str
    beat_count: int
    total_citations: int
    created_at: datetime
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True


class StreamingMessage(BaseModel):
    """Schema for streaming chat messages."""
    type: str  # "content", "citation", "complete", "error"
    content: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str  # "chat", "ping", "subscribe", "unsubscribe"
    message: Optional[str] = None
    episode_id: Optional[str] = None
    source_ids: Optional[List[str]] = None
    history: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None