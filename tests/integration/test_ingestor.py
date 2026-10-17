"""
Integration tests for DocumentIngestor
Uses mocks to avoid Qdrant dependencies
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


# Mock the SearchService to avoid import issues
@dataclass
class MockEmbeddingClient:
    def encode(self, texts):
        return [[0.1] * 384 for _ in texts]

@dataclass 
class MockQdrantClient:
    async def upsert(self, **kwargs):
        return True

@dataclass
class MockSearchService:
    """Mock SearchService for testing"""
    collection_name = "test_collection"
    
    def __init__(self):
        self.embedding_client = MockEmbeddingClient()
        self.qdrant_client = MockQdrantClient()
        self.index_document = AsyncMock(return_value=3)
        self.ensure_collection = AsyncMock(return_value=True)


@pytest.fixture
def mock_search_service():
    """Create mock SearchService"""
    return MockSearchService()


@pytest.fixture
def ingestor(mock_search_service):
    """Create DocumentIngestor with mock SearchService"""
    # Patch the import to avoid qdrant_client dependency
    with patch('ingest.ingestors.SearchService', return_value=mock_search_service):
        from ingest.ingestors import DocumentIngestor
        return DocumentIngestor(mock_search_service)


class TestDocumentIngestor:
    """Tests for DocumentIngestor"""
    
    @pytest.mark.asyncio
    async def test_ingestor_initialization(self, ingestor, mock_search_service):
        """Test ingestor initialization"""
        assert ingestor.search_service is mock_search_service
    
    @pytest.mark.asyncio
    async def test_ingest_text_file(self, ingestor, mock_search_service):
        """Test ingesting plain text file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("Test content")
            f.flush()
            temp_file = f.name
        
        try:
            result = await ingestor.ingest(temp_file)
            
            assert result.status == "success"
            assert result.file_type == ".txt"
            assert result.chunks_indexed == 3
            assert result.total_size > 0
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_ingest_markdown_file(self, ingestor, mock_search_service):
        """Test ingesting markdown file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("# Title\nContent here\n## Section\nMore content")
            f.flush()
            temp_file = f.name
        
        try:
            result = await ingestor.ingest(temp_file)
            
            assert result.status == "success"
            assert result.file_type == ".md"
            assert result.file_name.endswith('.md')
            # Markdown should have multiple chunks due to structure
            assert result.chunks_indexed > 0
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_ingest_openapi_file(self, ingestor, mock_search_service):
        """Test ingesting OpenAPI spec"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "getTest",
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(spec, f)
            f.flush()
            temp_file = f.name
        
        try:
            result = await ingestor.ingest(temp_file)
            
            assert result.status == "success"
            assert result.file_type == ".json"
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_ingest_unsupported_format(self, ingestor):
        """Test ingesting unsupported format"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.unknown',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("Test")
            f.flush()
            temp_file = f.name
        
        try:
            result = await ingestor.ingest(temp_file)
            
            assert result.status == "error"
            assert "Formato não suportado" in result.error_message
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_ingest_nonexistent_file(self, ingestor):
        """Test ingesting non-existent file"""
        result = await ingestor.ingest("/nonexistent/file.txt")
        
        assert result.status == "error"
        assert result.chunks_indexed == 0
    
    @pytest.mark.asyncio
    async def test_ingest_with_custom_doc_id(self, ingestor):
        """Test ingest with custom doc_id"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("Test content for doc")
            f.flush()
            temp_file = f.name
        
        try:
            custom_id = "my-custom-doc-id"
            result = await ingestor.ingest(temp_file, doc_id=custom_id)
            
            assert result.doc_id == custom_id
            assert result.status == "success"
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_ingest_batch(self, ingestor):
        """Test batch ingestion"""
        temp_files = []
        
        try:
            # Create test files
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.txt',
                    delete=False,
                    encoding='utf-8'
                ) as f:
                    f.write(f"Test content {i}")
                    f.flush()
                    temp_files.append(f.name)
            
            results = await ingestor.ingest_batch(temp_files)
            
            assert len(results) == 3
            assert all(r.status == "success" for r in results)
            assert sum(r.chunks_indexed for r in results) > 0
        finally:
            for f in temp_files:
                Path(f).unlink()
    
    @pytest.mark.asyncio
    async def test_ensure_ready(self, ingestor, mock_search_service):
        """Test ensuring system is ready"""
        ready = await ingestor.ensure_ready()
        
        assert ready is True
        await mock_search_service.ensure_collection()
    
    def test_get_supported_formats(self, ingestor):
        """Test getting supported formats"""
        formats = ingestor.get_supported_formats()
        
        assert ".txt" in formats
        assert ".md" in formats
        assert ".json" in formats


class TestIngestResultDataclass:
    """Tests for IngestResult dataclass"""
    
    def test_ingest_result_creation(self):
        """Test creating IngestResult"""
        from ingest.ingestors import IngestResult
        
        result = IngestResult(
            doc_id="test-123",
            file_name="test.md",
            file_path="/path/to/test.md",
            format=".md",
            chunks_indexed=5,
            total_size=1024,
            status="success",
        )
        
        assert result.doc_id == "test-123"
        assert result.file_name == "test.md"
        assert result.chunks_indexed == 5
        assert result.status == "success"
        assert result.error_message is None
    
    def test_ingest_result_with_error(self):
        """Test IngestResult with error"""
        from ingest.ingestors import IngestResult
        
        result = IngestResult(
            doc_id="test-123",
            file_name="test.md",
            file_path="/path/to/test.md",
            format=".md",
            chunks_indexed=0,
            total_size=0,
            status="error",
            error_message="Test error",
        )
        
        assert result.status == "error"
        assert result.error_message == "Test error"
        assert result.chunks_indexed == 0
