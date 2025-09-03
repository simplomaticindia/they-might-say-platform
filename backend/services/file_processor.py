"""
File processing service for document ingestion and text extraction.
Handles PDF, TXT, HTML, and other document formats.
"""
import os
import asyncio
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

import aiofiles
from fastapi import UploadFile
import PyPDF2
import textract
from bs4 import BeautifulSoup
import magic
from sqlalchemy.orm import Session

from models.source import Source
from models.document import Document
from models.chunk import Chunk
from services.text_chunker import TextChunker
from services.embeddings import EmbeddingsService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FileProcessor:
    """Handles file upload, processing, and text extraction."""
    
    def __init__(self, db: Session):
        self.db = db
        self.text_chunker = TextChunker()
        self.embeddings_service = EmbeddingsService()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Supported file types
        self.supported_types = {
            'application/pdf': self._process_pdf,
            'text/plain': self._process_text,
            'text/html': self._process_html,
            'application/msword': self._process_doc,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._process_docx,
        }
    
    async def process_upload(
        self, 
        file: UploadFile, 
        source_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Process uploaded file and create document record."""
        try:
            # Validate file
            await self._validate_file(file)
            
            # Save file to disk
            file_path = await self._save_file(file, source_id)
            
            # Extract text content
            content = await self._extract_text(file_path, file.content_type)
            
            # Create document record
            document = await self._create_document(
                file_path=file_path,
                source_id=source_id,
                filename=file.filename,
                content_type=file.content_type,
                content=content,
                metadata=metadata or {}
            )
            
            # Process chunks asynchronously
            asyncio.create_task(self._process_chunks(document))
            
            logger.info(f"Successfully processed file: {file.filename}")
            return document
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            raise
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file size
        if file.size > settings.MAX_UPLOAD_SIZE:
            raise ValueError(f"File too large: {file.size} bytes")
        
        # Check file type
        content_type = file.content_type
        if content_type not in self.supported_types:
            raise ValueError(f"Unsupported file type: {content_type}")
        
        # Additional security checks
        if not file.filename or '..' in file.filename:
            raise ValueError("Invalid filename")
    
    async def _save_file(self, file: UploadFile, source_id: str) -> Path:
        """Save uploaded file to disk."""
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = self._sanitize_filename(file.filename)
        filename = f"{source_id}_{timestamp}_{safe_filename}"
        
        file_path = self.upload_dir / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    async def _extract_text(self, file_path: Path, content_type: str) -> str:
        """Extract text content from file."""
        processor = self.supported_types.get(content_type)
        if not processor:
            raise ValueError(f"No processor for content type: {content_type}")
        
        return await processor(file_path)
    
    async def _process_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            if not text.strip():
                # Fallback to textract for complex PDFs
                text = textract.process(str(file_path)).decode('utf-8')
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            # Fallback to textract
            try:
                return textract.process(str(file_path)).decode('utf-8')
            except Exception as e2:
                logger.error(f"Textract also failed for {file_path}: {e2}")
                raise ValueError(f"Could not extract text from PDF: {e}")
    
    async def _process_text(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                        return await f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode text file")
    
    async def _process_html(self, file_path: Path) -> str:
        """Extract text from HTML file."""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            html_content = await f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def _process_doc(self, file_path: Path) -> str:
        """Extract text from DOC file."""
        try:
            return textract.process(str(file_path)).decode('utf-8')
        except Exception as e:
            logger.error(f"Error processing DOC {file_path}: {e}")
            raise ValueError(f"Could not extract text from DOC file: {e}")
    
    async def _process_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            return textract.process(str(file_path)).decode('utf-8')
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            raise ValueError(f"Could not extract text from DOCX file: {e}")
    
    async def _create_document(
        self,
        file_path: Path,
        source_id: str,
        filename: str,
        content_type: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Document:
        """Create document record in database."""
        # Calculate file hash
        file_hash = await self._calculate_file_hash(file_path)
        
        # Check for duplicates
        existing = self.db.query(Document).filter(
            Document.file_hash == file_hash
        ).first()
        
        if existing:
            logger.warning(f"Duplicate file detected: {filename}")
            return existing
        
        # Create document
        document = Document(
            source_id=source_id,
            filename=filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            file_hash=file_hash,
            content_type=content_type,
            content=content,
            word_count=len(content.split()),
            character_count=len(content),
            metadata=metadata,
            processing_status="completed"
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    async def _process_chunks(self, document: Document) -> None:
        """Process document into chunks and generate embeddings."""
        try:
            # Update processing status
            document.processing_status = "chunking"
            self.db.commit()
            
            # Create chunks
            chunks = self.text_chunker.chunk_text(
                text=document.content,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Process each chunk
            for i, chunk_text in enumerate(chunks):
                # Generate embedding
                embedding = await self.embeddings_service.generate_embedding(chunk_text)
                
                # Create chunk record
                chunk = Chunk(
                    document_id=document.id,
                    sequence_number=i,
                    content=chunk_text,
                    word_count=len(chunk_text.split()),
                    character_count=len(chunk_text),
                    embedding=embedding,
                    metadata={
                        "chunk_method": "recursive_character",
                        "chunk_size": settings.CHUNK_SIZE,
                        "chunk_overlap": settings.CHUNK_OVERLAP
                    }
                )
                
                self.db.add(chunk)
            
            # Update document status
            document.processing_status = "indexed"
            document.chunk_count = len(chunks)
            self.db.commit()
            
            logger.info(f"Successfully processed {len(chunks)} chunks for document {document.id}")
            
        except Exception as e:
            logger.error(f"Error processing chunks for document {document.id}: {e}")
            document.processing_status = "error"
            document.error_message = str(e)
            self.db.commit()
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            async for chunk in self._file_chunks(f):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _file_chunks(self, file, chunk_size: int = 8192):
        """Async generator for file chunks."""
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename
    
    def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """Get processing status for a document."""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"status": "not_found"}
        
        return {
            "status": document.processing_status,
            "chunk_count": document.chunk_count,
            "word_count": document.word_count,
            "error_message": document.error_message
        }
    
    async def reprocess_document(self, document_id: str) -> Document:
        """Reprocess a document (useful for failed processing)."""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # Clear existing chunks
        self.db.query(Chunk).filter(Chunk.document_id == document_id).delete()
        
        # Reset status
        document.processing_status = "processing"
        document.error_message = None
        self.db.commit()
        
        # Reprocess chunks
        await self._process_chunks(document)
        
        return document