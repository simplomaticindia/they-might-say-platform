"""
Citation tracking service for maintaining 100% citation coverage.
Tracks, validates, and manages citations across conversations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.citation import Citation
from models.chunk import Chunk
from models.source import Source
from models.document import Document
from models.episode import Episode
from models.beat import Beat

logger = logging.getLogger(__name__)


class CitationTracker:
    """Service for tracking and validating citations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def track_citations(
        self,
        episode_id: str,
        citations: List[Citation],
        response_text: str,
        beat_id: Optional[str] = None
    ) -> List[Citation]:
        """
        Track citations for a conversation response.
        
        Args:
            episode_id: Episode ID for the conversation
            citations: List of citation objects
            response_text: The full response text
            beat_id: Optional beat ID for granular tracking
            
        Returns:
            List of saved citation objects
        """
        try:
            saved_citations = []
            
            for citation in citations:
                # Set episode and beat references
                citation.episode_id = episode_id
                if beat_id:
                    citation.beat_id = beat_id
                
                # Add to database
                self.db.add(citation)
                saved_citations.append(citation)
            
            self.db.commit()
            
            # Update episode citation stats
            await self._update_episode_stats(episode_id)
            
            logger.info(f"Tracked {len(saved_citations)} citations for episode {episode_id}")
            return saved_citations
            
        except Exception as e:
            logger.error(f"Error tracking citations: {e}")
            self.db.rollback()
            raise
    
    async def validate_citation_accuracy(
        self,
        citation: Citation,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Validate that a citation accurately supports the claim in the response.
        
        Args:
            citation: Citation object to validate
            response_text: Full response text containing the claim
            
        Returns:
            Validation report with accuracy metrics
        """
        try:
            # Get the source chunk
            chunk = self.db.query(Chunk).filter(Chunk.id == citation.chunk_id).first()
            if not chunk:
                return {
                    "valid": False,
                    "error": "Source chunk not found",
                    "confidence": 0.0
                }
            
            # Extract the claim from response text around the citation
            claim_context = self._extract_claim_context(response_text, citation.citation_text)
            
            # Check semantic similarity between claim and source
            similarity_score = await self._calculate_claim_similarity(
                claim_context, 
                chunk.content
            )
            
            # Check for direct quotes
            quote_match = self._check_direct_quote(claim_context, chunk.content)
            
            # Validate source reliability
            source_reliability = chunk.document.source.reliability_score
            
            # Calculate overall accuracy score
            accuracy_score = self._calculate_accuracy_score(
                similarity_score,
                quote_match,
                source_reliability,
                citation.confidence_score
            )
            
            validation_report = {
                "valid": accuracy_score >= 0.7,
                "accuracy_score": accuracy_score,
                "similarity_score": similarity_score,
                "quote_match": quote_match,
                "source_reliability": source_reliability,
                "confidence": citation.confidence_score,
                "claim_context": claim_context,
                "source_snippet": chunk.content[:200] + "...",
                "validation_timestamp": datetime.now().isoformat()
            }
            
            # Update citation with validation results
            citation.validation_score = accuracy_score
            citation.validation_metadata = validation_report
            self.db.commit()
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Error validating citation: {e}")
            return {
                "valid": False,
                "error": str(e),
                "confidence": 0.0
            }
    
    async def get_episode_citation_report(self, episode_id: str) -> Dict[str, Any]:
        """Get comprehensive citation report for an episode."""
        try:
            # Get all citations for the episode
            citations = self.db.query(Citation).filter(
                Citation.episode_id == episode_id
            ).all()
            
            if not citations:
                return {
                    "episode_id": episode_id,
                    "total_citations": 0,
                    "coverage_percentage": 0,
                    "average_accuracy": 0,
                    "sources_used": 0,
                    "citations": []
                }
            
            # Calculate statistics
            total_citations = len(citations)
            valid_citations = sum(1 for c in citations if c.validation_score and c.validation_score >= 0.7)
            average_accuracy = sum(c.validation_score or 0 for c in citations) / total_citations
            
            # Get unique sources
            source_ids = set(c.source_id for c in citations)
            sources_used = len(source_ids)
            
            # Get source breakdown
            source_breakdown = {}
            for citation in citations:
                source_id = str(citation.source_id)
                if source_id not in source_breakdown:
                    source = citation.source
                    source_breakdown[source_id] = {
                        "title": source.title,
                        "author": source.author,
                        "reliability_score": source.reliability_score,
                        "citation_count": 0
                    }
                source_breakdown[source_id]["citation_count"] += 1
            
            return {
                "episode_id": episode_id,
                "total_citations": total_citations,
                "valid_citations": valid_citations,
                "coverage_percentage": (valid_citations / total_citations) * 100,
                "average_accuracy": average_accuracy,
                "sources_used": sources_used,
                "source_breakdown": source_breakdown,
                "citations": [
                    {
                        "id": str(c.id),
                        "citation_text": c.citation_text,
                        "confidence_score": c.confidence_score,
                        "validation_score": c.validation_score,
                        "source_title": c.source.title,
                        "created_at": c.created_at.isoformat()
                    }
                    for c in citations
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating citation report: {e}")
            raise
    
    async def get_source_citation_stats(self, source_id: str) -> Dict[str, Any]:
        """Get citation statistics for a specific source."""
        try:
            citations = self.db.query(Citation).filter(
                Citation.source_id == source_id
            ).all()
            
            if not citations:
                return {
                    "source_id": source_id,
                    "total_citations": 0,
                    "average_accuracy": 0,
                    "episodes_referenced": 0
                }
            
            total_citations = len(citations)
            average_accuracy = sum(c.validation_score or 0 for c in citations) / total_citations
            episodes_referenced = len(set(c.episode_id for c in citations if c.episode_id))
            
            # Get recent citations
            recent_citations = sorted(citations, key=lambda x: x.created_at, reverse=True)[:10]
            
            return {
                "source_id": source_id,
                "total_citations": total_citations,
                "average_accuracy": average_accuracy,
                "episodes_referenced": episodes_referenced,
                "recent_citations": [
                    {
                        "citation_text": c.citation_text,
                        "validation_score": c.validation_score,
                        "episode_id": str(c.episode_id) if c.episode_id else None,
                        "created_at": c.created_at.isoformat()
                    }
                    for c in recent_citations
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting source citation stats: {e}")
            raise
    
    async def find_similar_citations(
        self,
        citation_text: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar citations that have been used before."""
        try:
            # Simple text similarity for now - in production, use embeddings
            similar_citations = self.db.query(Citation).filter(
                Citation.citation_text.ilike(f"%{citation_text[:50]}%")
            ).limit(limit).all()
            
            return [
                {
                    "id": str(c.id),
                    "citation_text": c.citation_text,
                    "confidence_score": c.confidence_score,
                    "validation_score": c.validation_score,
                    "source_title": c.source.title,
                    "episode_id": str(c.episode_id) if c.episode_id else None,
                    "created_at": c.created_at.isoformat()
                }
                for c in similar_citations
            ]
            
        except Exception as e:
            logger.error(f"Error finding similar citations: {e}")
            return []
    
    async def _update_episode_stats(self, episode_id: str) -> None:
        """Update citation statistics for an episode."""
        try:
            episode = self.db.query(Episode).filter(Episode.id == episode_id).first()
            if not episode:
                return
            
            # Count citations
            citation_count = self.db.query(func.count(Citation.id)).filter(
                Citation.episode_id == episode_id
            ).scalar()
            
            # Calculate average accuracy
            avg_accuracy = self.db.query(func.avg(Citation.validation_score)).filter(
                Citation.episode_id == episode_id,
                Citation.validation_score.isnot(None)
            ).scalar()
            
            # Update episode metadata
            if not episode.metadata:
                episode.metadata = {}
            
            episode.metadata.update({
                "citation_count": citation_count,
                "average_citation_accuracy": float(avg_accuracy) if avg_accuracy else 0.0,
                "last_citation_update": datetime.now().isoformat()
            })
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating episode stats: {e}")
    
    def _extract_claim_context(self, response_text: str, citation_text: str) -> str:
        """Extract the context around a citation to identify the claim being made."""
        # Find the citation in the response
        citation_pos = response_text.find(citation_text)
        if citation_pos == -1:
            return ""
        
        # Extract surrounding sentences
        start = max(0, citation_pos - 200)
        end = min(len(response_text), citation_pos + len(citation_text) + 200)
        
        return response_text[start:end].strip()
    
    async def _calculate_claim_similarity(self, claim: str, source_content: str) -> float:
        """Calculate semantic similarity between claim and source content."""
        # Simplified version - in production, use embeddings similarity
        claim_words = set(claim.lower().split())
        source_words = set(source_content.lower().split())
        
        if not claim_words or not source_words:
            return 0.0
        
        intersection = claim_words.intersection(source_words)
        union = claim_words.union(source_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _check_direct_quote(self, claim: str, source_content: str) -> bool:
        """Check if the claim contains a direct quote from the source."""
        # Look for quoted text in the claim
        import re
        quotes = re.findall(r'"([^"]*)"', claim)
        
        for quote in quotes:
            if quote.lower() in source_content.lower():
                return True
        
        return False
    
    def _calculate_accuracy_score(
        self,
        similarity_score: float,
        quote_match: bool,
        source_reliability: float,
        confidence_score: float
    ) -> float:
        """Calculate overall accuracy score for a citation."""
        # Weighted combination of factors
        weights = {
            "similarity": 0.4,
            "quote_match": 0.3,
            "source_reliability": 0.2,
            "confidence": 0.1
        }
        
        quote_score = 1.0 if quote_match else 0.0
        
        accuracy = (
            weights["similarity"] * similarity_score +
            weights["quote_match"] * quote_score +
            weights["source_reliability"] * source_reliability +
            weights["confidence"] * confidence_score
        )
        
        return min(accuracy, 1.0)
    
    async def bulk_validate_citations(self, episode_id: str) -> Dict[str, Any]:
        """Validate all citations for an episode in bulk."""
        try:
            citations = self.db.query(Citation).filter(
                Citation.episode_id == episode_id
            ).all()
            
            validation_results = []
            
            for citation in citations:
                # Get the beat or episode content that contains this citation
                beat = self.db.query(Beat).filter(Beat.id == citation.beat_id).first()
                response_text = beat.lincoln_response if beat else ""
                
                if response_text:
                    validation = await self.validate_citation_accuracy(citation, response_text)
                    validation_results.append({
                        "citation_id": str(citation.id),
                        "validation": validation
                    })
            
            return {
                "episode_id": episode_id,
                "total_citations": len(citations),
                "validated_citations": len(validation_results),
                "results": validation_results
            }
            
        except Exception as e:
            logger.error(f"Error in bulk citation validation: {e}")
            raise