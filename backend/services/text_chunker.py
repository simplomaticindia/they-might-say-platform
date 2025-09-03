"""
Text chunking service for breaking documents into searchable segments.
Implements various chunking strategies optimized for historical documents.
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    method: str
    size: int
    overlap: int
    sequence: int
    word_count: int
    character_count: int
    has_citations: bool = False
    paragraph_count: int = 0


class TextChunker:
    """Advanced text chunking for historical documents."""
    
    def __init__(self):
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        
        # Paragraph patterns
        self.paragraph_breaks = re.compile(r'\n\s*\n')
        
        # Citation patterns (for historical documents)
        self.citation_patterns = [
            re.compile(r'\([^)]*\d{4}[^)]*\)'),  # (Author, 1865)
            re.compile(r'\[[^\]]*\d{4}[^\]]*\]'),  # [Author, 1865]
            re.compile(r'(?:p\.|pp\.|page|pages)\s*\d+'),  # page references
            re.compile(r'(?:vol\.|volume)\s*\d+'),  # volume references
        ]
        
        # Historical document markers
        self.document_markers = [
            re.compile(r'(?:letter|speech|address|proclamation|order)\s+(?:to|from|of)', re.IGNORECASE),
            re.compile(r'(?:dated|written|delivered)\s+(?:on\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)', re.IGNORECASE),
            re.compile(r'\b(?:18|19)\d{2}\b'),  # Years
        ]
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 100,
        method: str = "recursive_character"
    ) -> List[str]:
        """
        Chunk text using specified method.
        
        Args:
            text: Input text to chunk
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            method: Chunking method to use
        
        Returns:
            List of text chunks
        """
        if method == "recursive_character":
            return self._recursive_character_chunking(text, chunk_size, chunk_overlap)
        elif method == "sentence_aware":
            return self._sentence_aware_chunking(text, chunk_size, chunk_overlap)
        elif method == "paragraph_based":
            return self._paragraph_based_chunking(text, chunk_size, chunk_overlap)
        elif method == "semantic_sections":
            return self._semantic_section_chunking(text, chunk_size, chunk_overlap)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
    
    def _recursive_character_chunking(
        self, 
        text: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[str]:
        """
        Recursive character-based chunking with intelligent boundaries.
        Tries to break at natural boundaries (paragraphs, sentences, words).
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to find a good breaking point
            break_point = self._find_break_point(text, start, end)
            
            chunk = text[start:break_point]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = break_point - chunk_overlap
            if start < 0:
                start = 0
        
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find the best breaking point within the range."""
        # Look for paragraph breaks first
        search_text = text[max(0, end - 200):end + 100]
        paragraph_matches = list(self.paragraph_breaks.finditer(search_text))
        
        if paragraph_matches:
            # Find the closest paragraph break to our target
            target_pos = end - max(0, end - 200)
            best_match = min(paragraph_matches, key=lambda m: abs(m.start() - target_pos))
            return max(0, end - 200) + best_match.end()
        
        # Look for sentence breaks
        search_text = text[max(0, end - 100):end + 50]
        sentence_matches = list(self.sentence_endings.finditer(search_text))
        
        if sentence_matches:
            # Find the closest sentence break
            target_pos = end - max(0, end - 100)
            best_match = min(sentence_matches, key=lambda m: abs(m.start() - target_pos))
            return max(0, end - 100) + best_match.end()
        
        # Look for word boundaries
        for i in range(end, max(start, end - 50), -1):
            if text[i].isspace():
                return i
        
        # Fallback to exact position
        return end
    
    def _sentence_aware_chunking(
        self, 
        text: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[str]:
        """Chunk text by sentences, respecting chunk size limits."""
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence would exceed chunk size
            if current_size + sentence_size > chunk_size and current_chunk:
                # Finalize current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk, chunk_overlap)
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _paragraph_based_chunking(
        self, 
        text: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[str]:
        """Chunk text by paragraphs, combining when necessary."""
        paragraphs = self.paragraph_breaks.split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # If paragraph alone exceeds chunk size, split it
            if paragraph_size > chunk_size:
                # Finalize current chunk if it exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph
                sub_chunks = self._recursive_character_chunking(paragraph, chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                continue
            
            # If adding this paragraph would exceed chunk size
            if current_size + paragraph_size > chunk_size and current_chunk:
                # Finalize current chunk
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with potential overlap
                if chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    if len(overlap_text) <= chunk_overlap:
                        current_chunk = [overlap_text, paragraph]
                        current_size = len(overlap_text) + paragraph_size
                    else:
                        current_chunk = [paragraph]
                        current_size = paragraph_size
                else:
                    current_chunk = [paragraph]
                    current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size + 2  # Account for \n\n
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _semantic_section_chunking(
        self, 
        text: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[str]:
        """
        Chunk text based on semantic sections (for historical documents).
        Looks for document structure markers and natural divisions.
        """
        # First, identify potential section boundaries
        sections = self._identify_sections(text)
        
        if len(sections) <= 1:
            # No clear sections found, fall back to paragraph chunking
            return self._paragraph_based_chunking(text, chunk_size, chunk_overlap)
        
        chunks = []
        
        for section in sections:
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Section too large, chunk it further
                sub_chunks = self._paragraph_based_chunking(section, chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _identify_sections(self, text: str) -> List[str]:
        """Identify semantic sections in historical documents."""
        # Look for common section markers
        section_markers = [
            re.compile(r'^(?:CHAPTER|SECTION|PART)\s+[IVX\d]+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^[A-Z][A-Z\s]{10,}$', re.MULTILINE),  # ALL CAPS headers
            re.compile(r'^\d+\.\s+[A-Z]', re.MULTILINE),  # Numbered sections
            re.compile(r'^(?:Letter|Speech|Address|Proclamation|Order)\s+(?:to|from|of)', re.MULTILINE | re.IGNORECASE),
        ]
        
        boundaries = [0]  # Start of document
        
        for pattern in section_markers:
            for match in pattern.finditer(text):
                boundaries.append(match.start())
        
        boundaries.append(len(text))  # End of document
        boundaries = sorted(set(boundaries))
        
        sections = []
        for i in range(len(boundaries) - 1):
            section = text[boundaries[i]:boundaries[i + 1]].strip()
            if section:
                sections.append(section)
        
        return sections
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved accuracy."""
        # Handle common abbreviations that shouldn't end sentences
        abbreviations = ['Mr.', 'Mrs.', 'Dr.', 'Prof.', 'Gen.', 'Col.', 'Capt.', 'Lt.', 'Sgt.']
        
        # Temporarily replace abbreviations
        temp_text = text
        for i, abbr in enumerate(abbreviations):
            temp_text = temp_text.replace(abbr, f'__ABBR_{i}__')
        
        # Split on sentence endings
        sentences = self.sentence_endings.split(temp_text)
        
        # Restore abbreviations
        for i, abbr in enumerate(abbreviations):
            sentences = [s.replace(f'__ABBR_{i}__', abbr) for s in sentences]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_chars: int) -> List[str]:
        """Get sentences for overlap based on character count."""
        if not sentences or overlap_chars <= 0:
            return []
        
        overlap_sentences = []
        char_count = 0
        
        # Start from the end and work backwards
        for sentence in reversed(sentences):
            if char_count + len(sentence) <= overlap_chars:
                overlap_sentences.insert(0, sentence)
                char_count += len(sentence)
            else:
                break
        
        return overlap_sentences
    
    def analyze_chunk_quality(self, chunks: List[str]) -> Dict[str, Any]:
        """Analyze the quality of chunking results."""
        if not chunks:
            return {"error": "No chunks provided"}
        
        total_chars = sum(len(chunk) for chunk in chunks)
        chunk_sizes = [len(chunk) for chunk in chunks]
        
        # Count chunks with citations
        chunks_with_citations = 0
        for chunk in chunks:
            if any(pattern.search(chunk) for pattern in self.citation_patterns):
                chunks_with_citations += 1
        
        # Count chunks with historical markers
        chunks_with_markers = 0
        for chunk in chunks:
            if any(pattern.search(chunk) for pattern in self.document_markers):
                chunks_with_markers += 1
        
        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "average_chunk_size": total_chars / len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "chunks_with_citations": chunks_with_citations,
            "citation_coverage": chunks_with_citations / len(chunks),
            "chunks_with_historical_markers": chunks_with_markers,
            "historical_marker_coverage": chunks_with_markers / len(chunks),
        }
    
    def get_chunk_metadata(self, chunk: str, sequence: int, method: str) -> ChunkMetadata:
        """Generate metadata for a chunk."""
        word_count = len(chunk.split())
        character_count = len(chunk)
        paragraph_count = len(self.paragraph_breaks.split(chunk))
        
        # Check for citations
        has_citations = any(pattern.search(chunk) for pattern in self.citation_patterns)
        
        return ChunkMetadata(
            method=method,
            size=character_count,
            overlap=0,  # This would need to be calculated separately
            sequence=sequence,
            word_count=word_count,
            character_count=character_count,
            has_citations=has_citations,
            paragraph_count=paragraph_count
        )