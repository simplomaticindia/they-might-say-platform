"""
Studio Mode API endpoints for interactive Lincoln conversations.
Handles real-time chat, streaming responses, and episode management.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import get_current_user, require_role
from models.user import User
from models.episode import Episode
from models.beat import Beat
from services.rag_pipeline import RAGPipeline, StreamingRAGPipeline
from schemas.studio import (
    ConversationRequest, ConversationResponse, EpisodeCreate, 
    EpisodeResponse, BeatResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/studio", tags=["studio"])


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to Studio Mode")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from Studio Mode")
    
    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message))


manager = ConnectionManager()


@router.post("/conversation", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("host"))
):
    """Generate a Lincoln response to user message (non-streaming)."""
    try:
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(db)
        
        # Generate response
        result = await rag_pipeline.generate_response(
            user_message=request.message,
            conversation_history=request.conversation_history,
            source_ids=request.source_ids,
            episode_id=request.episode_id
        )
        
        # Create beat record if episode provided
        beat_id = None
        if request.episode_id:
            beat = Beat(
                episode_id=request.episode_id,
                sequence_number=request.sequence_number or 1,
                user_message=request.message,
                lincoln_response=result["response"],
                citations=result["citations"],
                metadata=result["metadata"]
            )
            db.add(beat)
            db.commit()
            db.refresh(beat)
            beat_id = str(beat.id)
        
        return ConversationResponse(
            response=result["response"],
            citations=result["citations"],
            beat_id=beat_id,
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Error in conversation endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.post("/conversation/stream")
async def stream_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("host"))
):
    """Generate streaming Lincoln response for real-time chat."""
    try:
        # Initialize streaming RAG pipeline
        streaming_pipeline = StreamingRAGPipeline(db)
        
        async def generate_stream():
            try:
                async for chunk in streaming_pipeline.generate_streaming_response(
                    user_message=request.message,
                    conversation_history=request.conversation_history,
                    source_ids=request.source_ids,
                    episode_id=request.episode_id
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error setting up streaming conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup streaming: {str(e)}"
        )


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time Studio Mode chat."""
    await manager.connect(websocket, user_id)
    
    try:
        streaming_pipeline = StreamingRAGPipeline(db)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                # Process chat message
                try:
                    async for chunk in streaming_pipeline.generate_streaming_response(
                        user_message=message_data["message"],
                        conversation_history=message_data.get("history", []),
                        source_ids=message_data.get("source_ids"),
                        episode_id=message_data.get("episode_id")
                    ):
                        await manager.send_message(user_id, chunk)
                        
                except Exception as e:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": str(e)
                    })
            
            elif message_data.get("type") == "ping":
                # Respond to ping
                await manager.send_message(user_id, {"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)


@router.post("/episodes", response_model=EpisodeResponse)
async def create_episode(
    episode_data: EpisodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("host"))
):
    """Create a new conversation episode."""
    try:
        episode = Episode(
            title=episode_data.title,
            description=episode_data.description,
            persona_pack_id=episode_data.persona_pack_id,
            created_by=current_user.id,
            status="active",
            metadata=episode_data.metadata or {}
        )
        
        db.add(episode)
        db.commit()
        db.refresh(episode)
        
        logger.info(f"Created episode: {episode.title} by user {current_user.username}")
        return episode
        
    except Exception as e:
        logger.error(f"Error creating episode: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create episode"
        )


@router.get("/episodes", response_model=List[EpisodeResponse])
async def list_episodes(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List conversation episodes."""
    try:
        query = db.query(Episode)
        
        # Filter by status if provided
        if status_filter:
            query = query.filter(Episode.status == status_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(Episode.created_at.desc())
        
        episodes = query.offset(skip).limit(limit).all()
        return episodes
        
    except Exception as e:
        logger.error(f"Error listing episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve episodes"
        )


@router.get("/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific episode with full details."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    return episode


@router.get("/episodes/{episode_id}/beats", response_model=List[BeatResponse])
async def get_episode_beats(
    episode_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation beats for an episode."""
    # Verify episode exists
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    try:
        beats = db.query(Beat).filter(
            Beat.episode_id == episode_id
        ).order_by(
            Beat.sequence_number.asc()
        ).offset(skip).limit(limit).all()
        
        return beats
        
    except Exception as e:
        logger.error(f"Error getting episode beats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation beats"
        )


@router.put("/episodes/{episode_id}/status")
async def update_episode_status(
    episode_id: UUID,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("host"))
):
    """Update episode status (active, paused, completed, archived)."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    # Check permissions
    if episode.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this episode"
        )
    
    valid_statuses = ["active", "paused", "completed", "archived"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    try:
        episode.status = status
        db.commit()
        
        logger.info(f"Updated episode {episode_id} status to {status}")
        return {"message": f"Episode status updated to {status}"}
        
    except Exception as e:
        logger.error(f"Error updating episode status: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update episode status"
        )


@router.get("/episodes/{episode_id}/export")
async def export_episode(
    episode_id: UUID,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export episode conversation in various formats."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    try:
        # Get all beats for the episode
        beats = db.query(Beat).filter(
            Beat.episode_id == episode_id
        ).order_by(Beat.sequence_number.asc()).all()
        
        if format == "json":
            export_data = {
                "episode": {
                    "id": str(episode.id),
                    "title": episode.title,
                    "description": episode.description,
                    "created_at": episode.created_at.isoformat(),
                    "status": episode.status
                },
                "conversation": [
                    {
                        "sequence": beat.sequence_number,
                        "user_message": beat.user_message,
                        "lincoln_response": beat.lincoln_response,
                        "citations": beat.citations,
                        "timestamp": beat.created_at.isoformat()
                    }
                    for beat in beats
                ]
            }
            
            return export_data
            
        elif format == "markdown":
            # Generate markdown format
            markdown_content = f"# {episode.title}\n\n"
            if episode.description:
                markdown_content += f"{episode.description}\n\n"
            
            markdown_content += f"**Created:** {episode.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            markdown_content += "---\n\n"
            
            for beat in beats:
                markdown_content += f"## Exchange {beat.sequence_number}\n\n"
                markdown_content += f"**User:** {beat.user_message}\n\n"
                markdown_content += f"**Lincoln:** {beat.lincoln_response}\n\n"
                
                if beat.citations:
                    markdown_content += "**Sources:**\n"
                    for citation in beat.citations:
                        markdown_content += f"- {citation.get('citation_text', 'Unknown source')}\n"
                    markdown_content += "\n"
                
                markdown_content += "---\n\n"
            
            return {"content": markdown_content, "format": "markdown"}
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use 'json' or 'markdown'"
            )
            
    except Exception as e:
        logger.error(f"Error exporting episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export episode"
        )


@router.get("/stats")
async def get_studio_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Studio Mode statistics and metrics."""
    try:
        from sqlalchemy import func
        
        # Episode stats
        total_episodes = db.query(func.count(Episode.id)).scalar()
        active_episodes = db.query(func.count(Episode.id)).filter(
            Episode.status == "active"
        ).scalar()
        
        # Beat stats
        total_beats = db.query(func.count(Beat.id)).scalar()
        
        # Citation stats
        from models.citation import Citation
        total_citations = db.query(func.count(Citation.id)).scalar()
        avg_citation_accuracy = db.query(func.avg(Citation.validation_score)).filter(
            Citation.validation_score.isnot(None)
        ).scalar()
        
        # Recent activity
        recent_episodes = db.query(Episode).order_by(
            Episode.created_at.desc()
        ).limit(5).all()
        
        return {
            "episodes": {
                "total": total_episodes,
                "active": active_episodes,
                "completed": db.query(func.count(Episode.id)).filter(
                    Episode.status == "completed"
                ).scalar()
            },
            "conversation": {
                "total_beats": total_beats,
                "total_citations": total_citations,
                "average_citation_accuracy": float(avg_citation_accuracy) if avg_citation_accuracy else 0.0
            },
            "recent_episodes": [
                {
                    "id": str(ep.id),
                    "title": ep.title,
                    "status": ep.status,
                    "created_at": ep.created_at.isoformat()
                }
                for ep in recent_episodes
            ],
            "active_connections": len(manager.active_connections)
        }
        
    except Exception as e:
        logger.error(f"Error getting studio stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get studio statistics"
        )