"""
Markdown Document Loader with Structure-Aware Parsing and Chunking
"""
import logging
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import aiofiles

from ingest.loader import BaseLoader, Document, DocumentMetadata


logger = logging.getLogger(__name__)


@dataclass
class HeadingHierarchy:
    """Tracks heading hierarchy for metadata"""
    h1: Optional[str] = None
    h2: Optional[str] = None
    h3: Optional[str] = None
    
    def update(self, level: int, text: str):
        """Update hierarchy based on heading level"""
        if level == 1:
            self.h1 = text
            self.h2 = None
            self.h3 = None
        elif level == 2:
            self.h2 = text
            self.h3 = None
        elif level == 3:
            self.h3 = text
    
    def to_dict(self) -> dict:
        """Convert to dictionary for metadata"""
        result = {}
        if self.h1:
            result['h1'] = self.h1
        if self.h2:
            result['h2'] = self.h2
        if self.h3:
            result['h3'] = self.h3
        return result
    
    def get_section(self) -> str:
        """Get current section path"""
        parts = []
        if self.h1:
            parts.append(self.h1)
        if self.h2:
            parts.append(self.h2)
        if self.h3:
            parts.append(self.h3)
        return ' > '.join(parts) if parts else 'root'


@dataclass
class MarkdownChunk:
    """Represents a chunk of markdown content"""
    content: str
    section: str
    heading_hierarchy: dict
    token_count: int = 0
    start_line: int = 0
    end_line: int = 0


class MarkdownParser:
    """Parse markdown while preserving structure"""
    
    # Heading pattern
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    # Approximate token count (words * 1.3)
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count using word count * 1.3"""
        words = len(text.split())
        return max(1, int(words * 1.3))
    
    def parse_structure(self, content: str) -> list[tuple[str, int]]:
        """Parse markdown structure, return (heading, level) tuples"""
        headings = []
        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((text, level))
        return headings
    
    def split_by_structure(self, content: str) -> list[dict]:
        """Split content by heading structure"""
        lines = content.split('\n')
        sections = []
        current_section = []
        hierarchy = HeadingHierarchy()
        start_line = 0
        
        for i, line in enumerate(lines):
            heading_match = self.HEADING_PATTERN.match(line)
            
            if heading_match:
                # Save previous section if it has content
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text:
                        sections.append({
                            'content': section_text,
                            'hierarchy': hierarchy.to_dict().copy(),
                            'section': hierarchy.get_section(),
                            'start_line': start_line,
                            'end_line': i - 1,
                        })
                    current_section = []
                
                # Update hierarchy
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                hierarchy.update(level, heading_text)
                
                # Start new section with heading
                current_section = [line]
                start_line = i
            else:
                current_section.append(line)
        
        # Don't forget last section
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:
                sections.append({
                    'content': section_text,
                    'hierarchy': hierarchy.to_dict().copy(),
                    'section': hierarchy.get_section(),
                    'start_line': start_line,
                    'end_line': len(lines) - 1,
                })
        
        return sections


class MarkdownChunker:
    """Split markdown sections into chunks with overlap"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap size in tokens between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_section(
        self,
        section: dict,
        section_index: int = 0
    ) -> list[MarkdownChunk]:
        """
        Chunk a markdown section into overlapping chunks.
        
        Args:
            section: Section dict from parser
            section_index: Index of this section
        
        Returns:
            List of MarkdownChunk objects
        """
        content = section['content']
        tokens = MarkdownParser.estimate_tokens(content)
        
        # If section is smaller than chunk size, return as single chunk
        if tokens <= self.chunk_size:
            return [
                MarkdownChunk(
                    content=content,
                    section=section['section'],
                    heading_hierarchy=section['hierarchy'],
                    token_count=tokens,
                    start_line=section['start_line'],
                    end_line=section['end_line'],
                )
            ]
        
        # Split into overlapping chunks
        chunks = []
        words = content.split()
        words_per_token = 1 / 1.3  # Reverse of estimation
        
        chunk_word_size = int(self.chunk_size * words_per_token)
        overlap_word_size = int(self.overlap * words_per_token)
        
        i = 0
        while i < len(words):
            # Take chunk_word_size words
            chunk_words = words[i:i + chunk_word_size]
            chunk_text = ' '.join(chunk_words)
            chunk_tokens = MarkdownParser.estimate_tokens(chunk_text)
            
            chunks.append(
                MarkdownChunk(
                    content=chunk_text,
                    section=section['section'],
                    heading_hierarchy=section['hierarchy'],
                    token_count=chunk_tokens,
                    start_line=section['start_line'],
                    end_line=section['end_line'],
                )
            )
            
            # Move forward by (chunk_word_size - overlap_word_size)
            i += chunk_word_size - overlap_word_size
        
        return chunks


class MarkdownLoader(BaseLoader):
    """Loader for Markdown files with structure-aware parsing"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize MarkdownLoader.
        
        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap size in tokens between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.parser = MarkdownParser()
        self.chunker = MarkdownChunker(chunk_size, overlap)
    
    async def load(self, file_path: str) -> Document:
        """
        Load and parse Markdown file.
        
        Args:
            file_path: Path to markdown file
        
        Returns:
            Document object with content and chunks
        """
        logger.info(f"Loading markdown file: {file_path}")
        
        path = Path(file_path)
        
        # Read file
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Parse structure
        sections = self.parser.split_by_structure(content)
        logger.info(f"Parsed {len(sections)} sections from {file_path}")
        
        # Chunk sections
        all_chunks = []
        for i, section in enumerate(sections):
            section_chunks = self.chunker.chunk_section(section, i)
            all_chunks.extend(section_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {file_path}")
        
        # Prepare metadata
        file_size = path.stat().st_size
        metadata = DocumentMetadata(
            file_path=str(path),
            file_name=path.name,
            file_size=file_size,
            file_type=".md",
            chunk_count=len(all_chunks),
            section_count=len(sections),
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )
        
        # Convert chunks to string list
        chunk_strings = [chunk.content for chunk in all_chunks]
        
        # Store chunks with metadata for later access
        self._last_chunks = all_chunks
        
        return Document(
            content=content,
            metadata=metadata,
            chunks=chunk_strings
        )
    
    async def validate(self, file_path: str) -> bool:
        """Validate that file is a markdown file"""
        return Path(file_path).suffix.lower() == ".md"
    
    def get_chunks_with_metadata(self) -> list[dict]:
        """
        Get chunks with full metadata.
        
        Returns:
            List of chunk dictionaries with metadata
        """
        if not hasattr(self, '_last_chunks'):
            return []
        
        return [
            {
                'content': chunk.content,
                'section': chunk.section,
                'heading_hierarchy': chunk.heading_hierarchy,
                'token_count': chunk.token_count,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
            }
            for chunk in self._last_chunks
        ]
