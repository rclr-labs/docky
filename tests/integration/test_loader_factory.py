"""
Integration tests for DocumentLoaderFactory
"""
import pytest
import tempfile
import json
from pathlib import Path

from ingest.loader import DocumentLoaderFactory, TextLoader, Document


class TestDocumentLoaderFactory:
    """Tests for DocumentLoaderFactory integration"""
    
    def test_get_loader_txt(self):
        """Test getting TextLoader"""
        loader = DocumentLoaderFactory.get_loader("test.txt")
        assert loader is not None
        assert isinstance(loader, TextLoader)
    
    def test_get_loader_md(self):
        """Test getting MarkdownLoader"""
        loader = DocumentLoaderFactory.get_loader("test.md")
        assert loader is not None
        assert loader.__class__.__name__ == "MarkdownLoader"
    
    def test_get_loader_json(self):
        """Test getting OpenAPILoader for JSON"""
        loader = DocumentLoaderFactory.get_loader("spec.json")
        assert loader is not None
        assert loader.__class__.__name__ == "OpenAPILoader"
    
    def test_get_loader_yaml(self):
        """Test getting OpenAPILoader for YAML"""
        loader = DocumentLoaderFactory.get_loader("spec.yaml")
        assert loader is not None
        assert loader.__class__.__name__ == "OpenAPILoader"
    
    def test_get_loader_unsupported(self):
        """Test getting loader for unsupported format"""
        loader = DocumentLoaderFactory.get_loader("test.unknown")
        assert loader is None
    
    def test_get_supported_formats(self):
        """Test getting list of supported formats"""
        formats = DocumentLoaderFactory.get_supported_formats()
        
        assert ".txt" in formats
        assert ".md" in formats
        assert ".json" in formats
        assert ".yaml" in formats
        assert ".yml" in formats
    
    def test_supports_format(self):
        """Test format support check"""
        assert DocumentLoaderFactory.supports_format(".txt")
        assert DocumentLoaderFactory.supports_format(".md")
        assert DocumentLoaderFactory.supports_format(".json")
        assert DocumentLoaderFactory.supports_format("yaml")  # Without dot
        
        assert not DocumentLoaderFactory.supports_format(".unknown")
        assert not DocumentLoaderFactory.supports_format("pdf")
    
    @pytest.mark.asyncio
    async def test_load_document_txt(self):
        """Test loading text file through factory"""
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
            doc = await DocumentLoaderFactory.load_document(temp_file)
            
            assert doc is not None
            assert isinstance(doc, Document)
            assert "Test content" in doc.content
            assert doc.metadata.file_type == ".txt"
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_load_document_md(self):
        """Test loading markdown file through factory"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("# Title\nContent here")
            f.flush()
            temp_file = f.name
        
        try:
            doc = await DocumentLoaderFactory.load_document(temp_file)
            
            assert doc is not None
            assert isinstance(doc, Document)
            assert "# Title" in doc.content
            assert doc.metadata.file_type == ".md"
            assert len(doc.chunks) > 0
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_load_document_json(self):
        """Test loading JSON OpenAPI spec through factory"""
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
            doc = await DocumentLoaderFactory.load_document(temp_file)
            
            assert doc is not None
            assert isinstance(doc, Document)
            assert doc.metadata.file_type == ".json"
            assert doc.metadata.api_title == "Test API"
            assert len(doc.chunks) > 0
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_load_document_invalid_file(self):
        """Test loading invalid file raises error"""
        with pytest.raises(FileNotFoundError):
            await DocumentLoaderFactory.load_document("/nonexistent/file.txt")
    
    @pytest.mark.asyncio
    async def test_load_document_unsupported_format(self):
        """Test loading unsupported format returns None"""
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
            doc = await DocumentLoaderFactory.load_document(temp_file)
            assert doc is None
        finally:
            Path(temp_file).unlink()
    
    def test_register_loader(self):
        """Test registering custom loader"""
        from ingest.loader import BaseLoader, Document, DocumentMetadata
        
        class CustomLoader(BaseLoader):
            async def load(self, file_path: str) -> Document:
                return Document(
                    content="custom",
                    metadata=DocumentMetadata(
                        file_path=file_path,
                        file_name="test",
                        file_size=0,
                        file_type=".custom"
                    )
                )
            
            async def validate(self, file_path: str) -> bool:
                return True
        
        # Register custom loader
        custom_loader = CustomLoader()
        DocumentLoaderFactory.register_loader(".custom", custom_loader)
        
        # Verify it's registered
        assert DocumentLoaderFactory.supports_format(".custom")
        loader = DocumentLoaderFactory.get_loader("test.custom")
        assert loader is custom_loader
