"""
Embeddings service for generating and managing vector embeddings.
Integrates with OpenAI's embedding models for semantic search.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json

import openai
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from config import get_settings
from models.chunk import Chunk

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingsService:
    """Service for generating and managing vector embeddings."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDINGS_MODEL
        self.dimension = settings.VECTOR_DIMENSION
        
        # Redis for caching embeddings
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Redis not available for embedding cache: {e}")
            self.redis_client = None
        
        # Rate limiting
        self.rate_limit_requests = 3000  # per minute
        self.rate_limit_tokens = 1000000  # per minute
        self.request_timestamps = []
        self.token_count = 0
        self.token_reset_time = datetime.now()
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Check cache first
        cached_embedding = await self._get_cached_embedding(text)
        if cached_embedding:
            return cached_embedding
        
        # Rate limiting
        await self._check_rate_limits(text)
        
        try:
            # Generate embedding
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            await self._cache_embedding(text, embedding)
            
            # Update rate limiting counters
            self._update_rate_limits(text)
            
            logger.debug(f"Generated embedding for text of length {len(text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Check cache for batch items
            batch_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for j, text in enumerate(batch):
                cached = await self._get_cached_embedding(text)
                if cached:
                    batch_embeddings.append(cached)
                else:
                    batch_embeddings.append(None)
                    uncached_texts.append(text)
                    uncached_indices.append(j)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                await self._check_rate_limits_batch(uncached_texts)
                
                try:
                    response = await self.client.embeddings.create(
                        model=self.model,
                        input=uncached_texts,
                        encoding_format="float"
                    )
                    
                    # Fill in the uncached embeddings
                    for k, embedding_data in enumerate(response.data):
                        original_index = uncached_indices[k]
                        embedding = embedding_data.embedding
                        batch_embeddings[original_index] = embedding
                        
                        # Cache the result
                        await self._cache_embedding(uncached_texts[k], embedding)
                    
                    # Update rate limiting
                    for text in uncached_texts:
                        self._update_rate_limits(text)
                    
                except Exception as e:
                    logger.error(f"Error generating batch embeddings: {e}")
                    raise
            
            embeddings.extend(batch_embeddings)
            
            # Small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings
    
    async def similarity_search(
        self, 
        db: Session,
        query_embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = 0.7,
        source_ids: Optional[List[str]] = None
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform similarity search using vector embeddings.
        
        Args:
            db: Database session
            query_embedding: Query vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            source_ids: Optional list of source IDs to filter by
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Convert embedding to string for SQL
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Build query
        query = """
        SELECT 
            chunks.*,
            1 - (chunks.embedding <=> %s::vector) as similarity
        FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        WHERE 1 - (chunks.embedding <=> %s::vector) >= %s
        """
        
        params = [embedding_str, embedding_str, similarity_threshold]
        
        # Add source filter if provided
        if source_ids:
            placeholders = ','.join(['%s'] * len(source_ids))
            query += f" AND documents.source_id IN ({placeholders})"
            params.extend(source_ids)
        
        query += " ORDER BY similarity DESC LIMIT %s"
        params.append(limit)
        
        # Execute query
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        # Convert to Chunk objects with similarity scores
        results = []
        for row in rows:
            chunk = db.query(Chunk).filter(Chunk.id == row.id).first()
            if chunk:
                results.append((chunk, float(row.similarity)))
        
        logger.debug(f"Found {len(results)} similar chunks")
        return results
    
    async def find_similar_chunks(
        self,
        db: Session,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        source_ids: Optional[List[str]] = None
    ) -> List[Tuple[Chunk, float]]:
        """
        Find chunks similar to query text.
        
        Args:
            db: Database session
            query_text: Text to search for
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            source_ids: Optional list of source IDs to filter by
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = await self.generate_embedding(query_text)
        
        # Perform similarity search
        return await self.similarity_search(
            db=db,
            query_embedding=query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold,
            source_ids=source_ids
        )
    
    async def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(text)
            cached = self.redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Error reading from embedding cache: {e}")
        
        return None
    
    async def _cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache embedding for future use."""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(text)
            # Cache for 7 days
            self.redis_client.setex(
                cache_key, 
                timedelta(days=7).total_seconds(), 
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"Error caching embedding: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        # Use hash of text + model name for cache key
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"embedding:{self.model}:{text_hash}"
    
    async def _check_rate_limits(self, text: str) -> None:
        """Check and enforce rate limits."""
        now = datetime.now()
        
        # Clean old timestamps (older than 1 minute)
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < timedelta(minutes=1)
        ]
        
        # Check request rate limit
        if len(self.request_timestamps) >= self.rate_limit_requests:
            sleep_time = 60 - (now - self.request_timestamps[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Check token rate limit
        if now - self.token_reset_time > timedelta(minutes=1):
            self.token_count = 0
            self.token_reset_time = now
        
        estimated_tokens = len(text.split()) * 1.3  # Rough estimate
        if self.token_count + estimated_tokens > self.rate_limit_tokens:
            sleep_time = 60 - (now - self.token_reset_time).total_seconds()
            if sleep_time > 0:
                logger.info(f"Token rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self.token_count = 0
                self.token_reset_time = datetime.now()
    
    async def _check_rate_limits_batch(self, texts: List[str]) -> None:
        """Check rate limits for batch processing."""
        total_tokens = sum(len(text.split()) * 1.3 for text in texts)
        
        now = datetime.now()
        
        # Reset token counter if needed
        if now - self.token_reset_time > timedelta(minutes=1):
            self.token_count = 0
            self.token_reset_time = now
        
        # Check if batch would exceed limits
        if self.token_count + total_tokens > self.rate_limit_tokens:
            sleep_time = 60 - (now - self.token_reset_time).total_seconds()
            if sleep_time > 0:
                logger.info(f"Batch would exceed token limit, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self.token_count = 0
                self.token_reset_time = datetime.now()
    
    def _update_rate_limits(self, text: str) -> None:
        """Update rate limiting counters."""
        self.request_timestamps.append(datetime.now())
        estimated_tokens = len(text.split()) * 1.3
        self.token_count += estimated_tokens
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics."""
        return {
            "model": self.model,
            "dimension": self.dimension,
            "recent_requests": len(self.request_timestamps),
            "current_token_count": self.token_count,
            "cache_available": self.redis_client is not None,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_tokens": self.rate_limit_tokens
        }
    
    async def validate_embedding_dimension(self, embedding: List[float]) -> bool:
        """Validate that embedding has correct dimensions."""
        return len(embedding) == self.dimension
    
    async def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have same dimensions")
        
        # Convert to numpy arrays for calculation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)