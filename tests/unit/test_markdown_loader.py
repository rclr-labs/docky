"""
Unit tests for Markdown Loader
"""
import pytest
import tempfile
from pathlib import Path

from ingest.loaders.markdown_loader import (
    MarkdownLoader,
    MarkdownParser,
    MarkdownChunker,
    HeadingHierarchy,
)


class TestHeadingHierarchy:
    """Tests for HeadingHierarchy class"""
    
    def test_initialization(self):
        """Test hierarchy initialization"""
        hierarchy = HeadingHierarchy()
        assert hierarchy.h1 is None
        assert hierarchy.h2 is None
        assert hierarchy.h3 is None
    
    def test_update_h1(self):
        """Test updating H1 heading"""
        hierarchy = HeadingHierarchy()
        hierarchy.update(1, "Main Title")
        assert hierarchy.h1 == "Main Title"
        assert hierarchy.h2 is None
        assert hierarchy.h3 is None
    
    def test_update_h2_clears_h3(self):
        """Test that updating H2 clears H3"""
        hierarchy = HeadingHierarchy()
        hierarchy.update(1, "Title")
        hierarchy.update(2, "Section")
        hierarchy.update(3, "Subsection")
        hierarchy.update(2, "New Section")
        
        assert hierarchy.h1 == "Title"
        assert hierarchy.h2 == "New Section"
        assert hierarchy.h3 is None
    
    def test_to_dict(self):
        """Test converting hierarchy to dict"""
        hierarchy = HeadingHierarchy()
        hierarchy.update(1, "Title")
        hierarchy.update(2, "Section")
        
        result = hierarchy.to_dict()
        assert result == {'h1': 'Title', 'h2': 'Section'}
    
    def test_get_section(self):
        """Test getting section path"""
        hierarchy = HeadingHierarchy()
        hierarchy.update(1, "Title")
        hierarchy.update(2, "Section")
        
        assert hierarchy.get_section() == "Title > Section"
    
    def test_get_section_root(self):
        """Test section path when empty"""
        hierarchy = HeadingHierarchy()
        assert hierarchy.get_section() == "root"


class TestMarkdownParser:
    """Tests for MarkdownParser class"""
    
    @pytest.fixture
    def parser(self):
        return MarkdownParser()
    
    def test_estimate_tokens_simple(self):
        """Test token estimation"""
        text = "This is a test"  # 4 words
        tokens = MarkdownParser.estimate_tokens(text)
        # 4 words * 1.3 = 5.2, should be 5
        assert tokens == 5
    
    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string"""
        tokens = MarkdownParser.estimate_tokens("")
        assert tokens == 1  # Minimum is 1
    
    def test_parse_structure_single_heading(self, parser):
        """Test parsing single heading"""
        content = "# Title\nSome content"
        headings = parser.parse_structure(content)
        
        assert len(headings) == 1
        assert headings[0] == ("Title", 1)
    
    def test_parse_structure_multiple_levels(self, parser):
        """Test parsing nested headings"""
        content = """# Main
## Section
### Subsection
## Another"""
        
        headings = parser.parse_structure(content)
        assert len(headings) == 4
        assert headings[0] == ("Main", 1)
        assert headings[1] == ("Section", 2)
        assert headings[2] == ("Subsection", 3)
        assert headings[3] == ("Another", 2)
    
    def test_split_by_structure_basic(self, parser):
        """Test basic structure splitting"""
        content = """# Title
Content here

## Section
Section content"""
        
        sections = parser.split_by_structure(content)
        
        assert len(sections) >= 1
        assert any("Title" in str(s) for s in sections)
    
    def test_split_by_structure_empty_sections(self, parser):
        """Test that empty sections are not created"""
        content = "# Title\n\n# Another"
        sections = parser.split_by_structure(content)
        
        # Should have at least the titled sections
        assert all(s['content'].strip() for s in sections)


class TestMarkdownChunker:
    """Tests for MarkdownChunker class"""
    
    @pytest.fixture
    def chunker(self):
        return MarkdownChunker(chunk_size=100, overlap=10)
    
    def test_initialization(self, chunker):
        """Test chunker initialization"""
        assert chunker.chunk_size == 100
        assert chunker.overlap == 10
    
    def test_chunk_small_section(self, chunker):
        """Test chunking a small section"""
        section = {
            'content': 'Small content with few words',
            'hierarchy': {'h1': 'Title'},
            'section': 'Title',
            'start_line': 0,
            'end_line': 0,
        }
        
        chunks = chunker.chunk_section(section)
        
        # Should create single chunk for small content
        assert len(chunks) == 1
        assert chunks[0].content == section['content']
        assert chunks[0].section == 'Title'
        assert chunks[0].heading_hierarchy == {'h1': 'Title'}
    
    def test_chunk_large_section(self, chunker):
        """Test chunking a large section"""
        # Create content larger than chunk_size
        large_text = " ".join(["word"] * 200)
        section = {
            'content': large_text,
            'hierarchy': {'h1': 'Title'},
            'section': 'Title',
            'start_line': 0,
            'end_line': 10,
        }
        
        chunks = chunker.chunk_section(section)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        # All chunks should have correct metadata
        for chunk in chunks:
            assert chunk.section == 'Title'
            assert chunk.heading_hierarchy == {'h1': 'Title'}
    
    def test_chunk_overlap(self, chunker):
        """Test that chunks have overlap"""
        large_text = " ".join([f"word{i}" for i in range(300)])
        section = {
            'content': large_text,
            'hierarchy': {},
            'section': 'root',
            'start_line': 0,
            'end_line': 0,
        }
        
        chunks = chunker.chunk_section(section)
        
        # Check that consecutive chunks have some word overlap
        if len(chunks) > 1:
            # Extract words from consecutive chunks
            chunk1_words = set(chunks[0].content.split())
            chunk2_words = set(chunks[1].content.split())
            
            # There should be some overlap
            overlap = chunk1_words & chunk2_words
            assert len(overlap) > 0


class TestMarkdownLoader:
    """Tests for MarkdownLoader class"""
    
    @pytest.fixture
    def loader(self):
        return MarkdownLoader(chunk_size=256, overlap=25)
    
    @pytest.fixture
    def markdown_file(self):
        """Create a temporary markdown file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as f:
            content = """# Introduction
This is the introduction section with some content.

## Getting Started
Follow these steps to get started.
1. Install the package
2. Configure settings
3. Run the application

### Installation
Install using pip: `pip install package`

## Advanced Usage
This section covers advanced features.

### Custom Configuration
Configure the system by editing config.json
"""
            f.write(content)
            f.flush()
            yield f.name
        
        # Cleanup
        Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_validate_markdown_file(self, loader):
        """Test validation of markdown files"""
        assert await loader.validate("test.md")
        assert not await loader.validate("test.txt")
        assert not await loader.validate("test.pdf")
    
    @pytest.mark.asyncio
    async def test_load_markdown(self, loader, markdown_file):
        """Test loading markdown file"""
        doc = await loader.load(markdown_file)
        
        assert doc.content is not None
        assert doc.metadata.file_type == ".md"
        assert doc.metadata.file_name.endswith('.md')
        assert len(doc.chunks) > 0
    
    @pytest.mark.asyncio
    async def test_load_preserves_structure(self, loader, markdown_file):
        """Test that loading preserves markdown structure"""
        doc = await loader.load(markdown_file)
        
        # Content should contain original markdown
        assert "# Introduction" in doc.content
        assert "## Getting Started" in doc.content
        
        # Chunks should not be empty
        for chunk in doc.chunks:
            assert len(chunk.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_load_creates_chunks(self, loader, markdown_file):
        """Test that loading creates appropriate chunks"""
        doc = await loader.load(markdown_file)
        
        # Should have chunk metadata
        assert hasattr(doc.metadata, 'chunk_count')
        assert doc.metadata.chunk_count > 0
        assert len(doc.chunks) == doc.metadata.chunk_count
    
    @pytest.mark.asyncio
    async def test_get_chunks_with_metadata(self, loader, markdown_file):
        """Test getting chunks with full metadata"""
        doc = await loader.load(markdown_file)
        chunks = loader.get_chunks_with_metadata()
        
        assert len(chunks) > 0
        
        # Check chunk structure
        for chunk in chunks:
            assert 'content' in chunk
            assert 'section' in chunk
            assert 'heading_hierarchy' in chunk
            assert 'token_count' in chunk
            assert chunk['token_count'] > 0
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, loader):
        """Test loading a non-existent file"""
        with pytest.raises(FileNotFoundError):
            await loader.load("/nonexistent/file.md")
    
    @pytest.mark.asyncio
    async def test_chunk_size_configuration(self):
        """Test that chunk size is configurable"""
        loader_small = MarkdownLoader(chunk_size=100, overlap=10)
        loader_large = MarkdownLoader(chunk_size=1000, overlap=100)
        
        assert loader_small.chunk_size == 100
        assert loader_large.chunk_size == 1000
