"""
Source management API endpoints.
Handles source creation, document upload, and processing status.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import get_current_user, require_role
from models.user import User
from models.source import Source
from models.document import Document
from services.file_processor import FileProcessor
from schemas.source import SourceCreate, SourceResponse, SourceUpdate
from schemas.document import DocumentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=SourceResponse)
async def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("producer"))
):
    """Create a new source."""
    try:
        # Check if source with same title exists
        existing = db.query(Source).filter(
            Source.title == source_data.title,
            Source.created_by == current_user.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Source with this title already exists"
            )
        
        # Create source
        source = Source(
            title=source_data.title,
            description=source_data.description,
            source_type=source_data.source_type,
            author=source_data.author,
            publication_date=source_data.publication_date,
            publisher=source_data.publisher,
            isbn=source_data.isbn,
            url=source_data.url,
            reliability_score=source_data.reliability_score,
            tags=source_data.tags,
            metadata=source_data.metadata or {},
            created_by=current_user.id
        )
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        logger.info(f"Created source: {source.title} by user {current_user.username}")
        return source
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating source: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create source"
        )


@router.get("/", response_model=List[SourceResponse])
async def list_sources(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    source_type: Optional[str] = None,
    tags: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sources with optional filtering."""
    try:
        query = db.query(Source)
        
        # Apply filters
        if search:
            query = query.filter(
                Source.title.ilike(f"%{search}%") |
                Source.description.ilike(f"%{search}%") |
                Source.author.ilike(f"%{search}%")
            )
        
        if source_type:
            query = query.filter(Source.source_type == source_type)
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.filter(Source.tags.ilike(f"%{tag}%"))
        
        # Order by creation date (newest first)
        query = query.order_by(Source.created_at.desc())
        
        # Apply pagination
        sources = query.offset(skip).limit(limit).all()
        
        return sources
        
    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sources"
        )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific source by ID."""
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    return source


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    source_update: SourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("producer"))
):
    """Update a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Check permissions (only creator or admin can update)
    if source.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this source"
        )
    
    try:
        # Update fields
        update_data = source_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)
        
        db.commit()
        db.refresh(source)
        
        logger.info(f"Updated source: {source.title} by user {current_user.username}")
        return source
        
    except Exception as e:
        logger.error(f"Error updating source: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update source"
        )


@router.delete("/{source_id}")
async def delete_source(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("producer"))
):
    """Delete a source and all associated documents."""
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Check permissions (only creator or admin can delete)
    if source.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this source"
        )
    
    try:
        # Delete associated documents and chunks (cascade should handle this)
        db.delete(source)
        db.commit()
        
        logger.info(f"Deleted source: {source.title} by user {current_user.username}")
        return {"message": "Source deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete source"
        )


@router.post("/{source_id}/upload", response_model=DocumentResponse)
async def upload_document(
    source_id: UUID,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("producer"))
):
    """Upload a document to a source."""
    # Verify source exists
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Check permissions
    if source.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this source"
        )
    
    try:
        # Parse metadata if provided
        doc_metadata = {}
        if metadata:
            import json
            try:
                doc_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid metadata JSON"
                )
        
        # Process file
        file_processor = FileProcessor(db)
        document = await file_processor.process_upload(
            file=file,
            source_id=str(source_id),
            metadata=doc_metadata
        )
        
        logger.info(f"Uploaded document: {file.filename} to source {source.title}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{source_id}/documents", response_model=List[DocumentResponse])
async def list_source_documents(
    source_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents for a specific source."""
    # Verify source exists
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    try:
        documents = db.query(Document).filter(
            Document.source_id == source_id
        ).order_by(
            Document.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return documents
        
    except Exception as e:
        logger.error(f"Error listing source documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{source_id}/processing-status")
async def get_processing_status(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get processing status for all documents in a source."""
    # Verify source exists
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    try:
        documents = db.query(Document).filter(Document.source_id == source_id).all()
        
        status_summary = {
            "total_documents": len(documents),
            "completed": 0,
            "processing": 0,
            "chunking": 0,
            "indexed": 0,
            "error": 0,
            "documents": []
        }
        
        for doc in documents:
            status_summary[doc.processing_status] += 1
            status_summary["documents"].append({
                "id": str(doc.id),
                "filename": doc.filename,
                "status": doc.processing_status,
                "chunk_count": doc.chunk_count,
                "error_message": doc.error_message,
                "created_at": doc.created_at.isoformat()
            })
        
        return status_summary
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing status"
        )


@router.post("/{source_id}/reprocess")
async def reprocess_source_documents(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("producer"))
):
    """Reprocess all documents in a source."""
    # Verify source exists
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Check permissions
    if source.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reprocess this source"
        )
    
    try:
        file_processor = FileProcessor(db)
        documents = db.query(Document).filter(Document.source_id == source_id).all()
        
        reprocessed_count = 0
        for document in documents:
            try:
                await file_processor.reprocess_document(str(document.id))
                reprocessed_count += 1
            except Exception as e:
                logger.error(f"Error reprocessing document {document.id}: {e}")
        
        logger.info(f"Reprocessed {reprocessed_count} documents for source {source.title}")
        return {
            "message": f"Started reprocessing {reprocessed_count} documents",
            "total_documents": len(documents),
            "reprocessed": reprocessed_count
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing source documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess documents"
        )


@router.get("/{source_id}/stats")
async def get_source_stats(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a source."""
    # Verify source exists
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    try:
        from sqlalchemy import func
        
        # Get document stats
        doc_stats = db.query(
            func.count(Document.id).label('total_documents'),
            func.sum(Document.word_count).label('total_words'),
            func.sum(Document.character_count).label('total_characters'),
            func.sum(Document.chunk_count).label('total_chunks')
        ).filter(Document.source_id == source_id).first()
        
        # Get processing status breakdown
        status_breakdown = db.query(
            Document.processing_status,
            func.count(Document.id).label('count')
        ).filter(
            Document.source_id == source_id
        ).group_by(Document.processing_status).all()
        
        status_dict = {status: count for status, count in status_breakdown}
        
        return {
            "source_id": str(source_id),
            "source_title": source.title,
            "total_documents": doc_stats.total_documents or 0,
            "total_words": doc_stats.total_words or 0,
            "total_characters": doc_stats.total_characters or 0,
            "total_chunks": doc_stats.total_chunks or 0,
            "processing_status": status_dict,
            "reliability_score": source.reliability_score,
            "created_at": source.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting source stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get source statistics"
        )