"""
RAG (Retrieval-Augmented Generation) Pipeline for Abraham Lincoln conversations.
Handles context retrieval, prompt engineering, and response generation with citations.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

import openai
from sqlalchemy.orm import Session

from config import get_settings
from models.chunk import Chunk
from models.source import Source
from models.document import Document
from models.citation import Citation
from services.embeddings import EmbeddingsService
from services.citation_tracker import CitationTracker

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGPipeline:
    """RAG pipeline for generating historically accurate Lincoln responses."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embeddings_service = EmbeddingsService()
        self.citation_tracker = CitationTracker(db)
        
        # Configuration
        self.model = settings.LLM_MODEL
        self.max_context_chunks = 10
        self.similarity_threshold = 0.7
        self.max_tokens = 1000
        self.temperature = 0.7
        
        # Lincoln persona prompt
        self.system_prompt = self._build_system_prompt()
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        source_ids: Optional[List[str]] = None,
        episode_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from Abraham Lincoln with full citation coverage.
        
        Args:
            user_message: The user's question or message
            conversation_history: Previous conversation context
            source_ids: Optional list of source IDs to search within
            episode_id: Optional episode ID for tracking
            
        Returns:
            Dictionary containing response, citations, and metadata
        """
        try:
            logger.info(f"Generating Lincoln response for: {user_message[:100]}...")
            
            # Step 1: Retrieve relevant context
            context_chunks = await self._retrieve_context(
                query=user_message,
                source_ids=source_ids,
                max_chunks=self.max_context_chunks
            )
            
            # Step 2: Build prompt with context and history
            prompt = await self._build_prompt(
                user_message=user_message,
                context_chunks=context_chunks,
                conversation_history=conversation_history or []
            )
            
            # Step 3: Generate response
            response_text = await self._generate_llm_response(prompt)
            
            # Step 4: Extract and validate citations
            citations = await self._extract_citations(response_text, context_chunks)
            
            # Step 5: Validate citation coverage
            coverage_report = await self._validate_citation_coverage(response_text, citations)
            
            # Step 6: Track citations if episode provided
            if episode_id:
                await self.citation_tracker.track_citations(
                    episode_id=episode_id,
                    citations=citations,
                    response_text=response_text
                )
            
            result = {
                "response": response_text,
                "citations": [citation.to_dict() for citation in citations],
                "context_chunks_used": len(context_chunks),
                "citation_coverage": coverage_report,
                "metadata": {
                    "model": self.model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "timestamp": datetime.now().isoformat(),
                    "sources_searched": len(set(chunk.document.source_id for chunk in context_chunks))
                }
            }
            
            logger.info(f"Generated response with {len(citations)} citations")
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            raise
    
    async def _retrieve_context(
        self,
        query: str,
        source_ids: Optional[List[str]] = None,
        max_chunks: int = 10
    ) -> List[Chunk]:
        """Retrieve relevant context chunks for the query."""
        try:
            # Find similar chunks
            similar_chunks = await self.embeddings_service.find_similar_chunks(
                db=self.db,
                query_text=query,
                limit=max_chunks * 2,  # Get more to filter
                similarity_threshold=self.similarity_threshold,
                source_ids=source_ids
            )
            
            # Sort by similarity and take top chunks
            sorted_chunks = sorted(similar_chunks, key=lambda x: x[1], reverse=True)
            
            # Filter for diversity (avoid too many chunks from same document)
            selected_chunks = []
            document_counts = {}
            
            for chunk, similarity in sorted_chunks:
                doc_id = chunk.document_id
                if document_counts.get(doc_id, 0) < 3:  # Max 3 chunks per document
                    selected_chunks.append(chunk)
                    document_counts[doc_id] = document_counts.get(doc_id, 0) + 1
                    
                    if len(selected_chunks) >= max_chunks:
                        break
            
            logger.debug(f"Retrieved {len(selected_chunks)} context chunks")
            return selected_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    async def _build_prompt(
        self,
        user_message: str,
        context_chunks: List[Chunk],
        conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Build the complete prompt for the LLM."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        for exchange in conversation_history[-5:]:  # Last 5 exchanges
            if exchange.get("user"):
                messages.append({"role": "user", "content": exchange["user"]})
            if exchange.get("assistant"):
                messages.append({"role": "assistant", "content": exchange["assistant"]})
        
        # Build context section
        context_text = await self._format_context(context_chunks)
        
        # Build the current user message with context
        user_prompt = f"""Based on the following historical sources, please respond as Abraham Lincoln would have, addressing the user's question or comment.

HISTORICAL SOURCES:
{context_text}

USER MESSAGE: {user_message}

Please respond in character as Abraham Lincoln, using the provided sources to inform your response. Include specific citations in the format [Source: Title, Page/Location] for any factual claims or quotes. Maintain Lincoln's thoughtful, measured speaking style while making the content accessible to modern readers."""
        
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    async def _format_context(self, chunks: List[Chunk]) -> str:
        """Format context chunks for the prompt."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Get source and document info
            document = chunk.document
            source = document.source
            
            # Format the context entry
            context_entry = f"""
[{i}] Source: {source.title}
Author: {source.author or 'Unknown'}
Type: {source.source_type}
Reliability: {source.reliability_score:.1f}/1.0
Content: {chunk.content}
---"""
            context_parts.append(context_entry)
        
        return "\n".join(context_parts)
    
    async def _generate_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response from the LLM."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    async def _extract_citations(
        self,
        response_text: str,
        context_chunks: List[Chunk]
    ) -> List[Citation]:
        """Extract and create citation objects from the response."""
        citations = []
        
        # Find citation patterns in the response
        import re
        citation_pattern = r'\[Source: ([^\]]+)\]'
        citation_matches = re.findall(citation_pattern, response_text)
        
        # Match citations to actual sources
        for citation_text in citation_matches:
            # Try to match to a context chunk
            best_match = None
            best_score = 0
            
            for chunk in context_chunks:
                source = chunk.document.source
                title_match = citation_text.lower() in source.title.lower()
                author_match = source.author and source.author.lower() in citation_text.lower()
                
                score = 0
                if title_match:
                    score += 2
                if author_match:
                    score += 1
                
                if score > best_score:
                    best_match = chunk
                    best_score = score
            
            if best_match:
                citation = Citation(
                    chunk_id=best_match.id,
                    source_id=best_match.document.source_id,
                    document_id=best_match.document_id,
                    citation_text=citation_text,
                    context_snippet=best_match.content[:200] + "...",
                    confidence_score=min(best_score / 3.0, 1.0),
                    metadata={
                        "extraction_method": "pattern_matching",
                        "original_text": citation_text
                    }
                )
                citations.append(citation)
        
        return citations
    
    async def _validate_citation_coverage(
        self,
        response_text: str,
        citations: List[Citation]
    ) -> Dict[str, Any]:
        """Validate that all factual claims are properly cited."""
        # This is a simplified version - in production, you'd want more sophisticated
        # fact extraction and validation
        
        # Count sentences and citations
        sentences = response_text.split('.')
        factual_sentences = [s for s in sentences if self._is_factual_claim(s)]
        
        coverage_percentage = min(len(citations) / max(len(factual_sentences), 1), 1.0) * 100
        
        return {
            "total_sentences": len(sentences),
            "factual_claims": len(factual_sentences),
            "citations_provided": len(citations),
            "coverage_percentage": coverage_percentage,
            "meets_requirement": coverage_percentage >= 90,  # 90% threshold
            "missing_citations": max(0, len(factual_sentences) - len(citations))
        }
    
    def _is_factual_claim(self, sentence: str) -> bool:
        """Determine if a sentence contains a factual claim that needs citation."""
        # Simple heuristics - in production, use NLP models
        factual_indicators = [
            'in', 'on', 'during', 'said', 'wrote', 'declared',
            'signed', 'passed', 'enacted', 'established',
            'born', 'died', 'elected', 'appointed'
        ]
        
        sentence_lower = sentence.lower()
        return any(indicator in sentence_lower for indicator in factual_indicators)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for Abraham Lincoln persona."""
        return """You are Abraham Lincoln, the 16th President of the United States, speaking in the modern era but maintaining your historical perspective and wisdom. Your responses should:

PERSONALITY & STYLE:
- Speak with Lincoln's characteristic thoughtfulness, humility, and measured wisdom
- Use accessible modern English while maintaining dignity and gravitas
- Include occasional folksy analogies or stories when appropriate
- Show empathy, moral clarity, and practical wisdom
- Demonstrate Lincoln's dry humor when suitable

HISTORICAL ACCURACY:
- Base all factual claims on the provided historical sources
- Cite sources for any specific facts, quotes, or historical references
- If uncertain about a fact, acknowledge the limitation honestly
- Maintain historical perspective while addressing modern questions

CITATION REQUIREMENTS:
- Every factual claim must include a citation in format: [Source: Title, Page/Location]
- Quote directly from sources when possible
- If paraphrasing, still provide citation
- Never make unsupported historical claims

CONVERSATION APPROACH:
- Listen carefully to the user's question or concern
- Provide thoughtful, substantive responses
- Connect historical lessons to contemporary issues when relevant
- Encourage reflection and deeper thinking
- Maintain respect for all people while staying true to historical context

Remember: You are not just reciting history, but engaging as Lincoln would - with wisdom, compassion, and moral clarity, always grounded in verifiable historical sources."""

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG pipeline performance."""
        return {
            "model": self.model,
            "max_context_chunks": self.max_context_chunks,
            "similarity_threshold": self.similarity_threshold,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "embeddings_service": self.embeddings_service.get_embedding_stats()
        }
    
    async def update_configuration(self, config: Dict[str, Any]) -> None:
        """Update pipeline configuration."""
        if "max_context_chunks" in config:
            self.max_context_chunks = config["max_context_chunks"]
        if "similarity_threshold" in config:
            self.similarity_threshold = config["similarity_threshold"]
        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]
        if "temperature" in config:
            self.temperature = config["temperature"]
        
        logger.info(f"Updated RAG pipeline configuration: {config}")


class StreamingRAGPipeline(RAGPipeline):
    """Streaming version of RAG pipeline for real-time responses."""
    
    async def generate_streaming_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        source_ids: Optional[List[str]] = None,
        episode_id: Optional[str] = None
    ):
        """Generate streaming response for real-time chat."""
        try:
            # Retrieve context (same as regular pipeline)
            context_chunks = await self._retrieve_context(
                query=user_message,
                source_ids=source_ids,
                max_chunks=self.max_context_chunks
            )
            
            # Build prompt
            prompt = await self._build_prompt(
                user_message=user_message,
                context_chunks=context_chunks,
                conversation_history=conversation_history or []
            )
            
            # Stream response
            response_stream = await self.client.chat.completions.create(
                model=self.model,
                messages=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            # Yield chunks as they come
            full_response = ""
            async for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield {
                        "type": "content",
                        "content": content,
                        "full_response": full_response
                    }
            
            # Process citations after full response
            citations = await self._extract_citations(full_response, context_chunks)
            coverage_report = await self._validate_citation_coverage(full_response, citations)
            
            # Track citations
            if episode_id:
                await self.citation_tracker.track_citations(
                    episode_id=episode_id,
                    citations=citations,
                    response_text=full_response
                )
            
            # Send final metadata
            yield {
                "type": "complete",
                "citations": [citation.to_dict() for citation in citations],
                "coverage_report": coverage_report,
                "metadata": {
                    "context_chunks_used": len(context_chunks),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in streaming RAG pipeline: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }