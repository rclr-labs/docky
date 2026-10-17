"""
Unit tests for OpenAPI Loader
"""
import pytest
import tempfile
import json
from pathlib import Path

from ingest.loaders.openapi_loader import (
    OpenAPILoader,
    OpenAPIParser,
    OpenAPIOperation,
)


# Sample OpenAPI 3.0 specification
SAMPLE_OPENAPI_JSON = {
    "openapi": "3.0.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
        "description": "A sample API that uses pets"
    },
    "servers": [
        {"url": "https://api.example.com"}
    ],
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "description": "Returns a list of pets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return",
                        "required": False,
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A paged array of pets"
                    },
                    "default": {
                        "description": "unexpected error"
                    }
                }
            },
            "post": {
                "operationId": "createPets",
                "summary": "Create a pet",
                "tags": ["pets"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    },
                    "required": True
                },
                "responses": {
                    "201": {
                        "description": "Null response"
                    }
                }
            }
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "showPetById",
                "summary": "Info for a specific pet",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "description": "The id of the pet",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Expected response to a valid request"
                    }
                }
            }
        }
    }
}

# Sample OpenAPI with multiple tags
SAMPLE_OPENAPI_MULTI_TAG = {
    "openapi": "3.0.1",
    "info": {
        "title": "User API",
        "version": "2.0.0"
    },
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "tags": ["users", "public"],
                "summary": "List users",
                "responses": {
                    "200": {"description": "Success"}
                }
            },
            "post": {
                "operationId": "createUser",
                "tags": ["users", "admin"],
                "summary": "Create user",
                "responses": {
                    "201": {"description": "Created"}
                }
            }
        }
    }
}


class TestOpenAPIOperation:
    """Tests for OpenAPIOperation class"""
    
    def test_initialization(self):
        """Test operation initialization"""
        op = OpenAPIOperation(
            path="/users",
            method="get",
            operation_id="listUsers",
            summary="List all users"
        )
        
        assert op.path == "/users"
        assert op.method == "get"
        assert op.operation_id == "listUsers"
        assert op.summary == "List all users"
        assert op.tags == []
    
    def test_to_text(self):
        """Test converting operation to text"""
        op = OpenAPIOperation(
            path="/users",
            method="post",
            operation_id="createUser",
            summary="Create a user",
            tags=["users"]
        )
        
        text = op.to_text()
        
        assert "POST /users" in text
        assert "createUser" in text
        assert "Create a user" in text
        assert "users" in text
    
    def test_to_text_with_parameters(self):
        """Test converting operation with parameters to text"""
        op = OpenAPIOperation(
            path="/pets/{petId}",
            method="get",
            operation_id="showPetById",
            parameters={
                "petId": {
                    "type": "string",
                    "required": True,
                    "description": "The pet ID"
                }
            }
        )
        
        text = op.to_text()
        
        assert "petId" in text
        assert "required" in text
        assert "The pet ID" in text


class TestOpenAPIParser:
    """Tests for OpenAPIParser class"""
    
    @pytest.fixture
    def parser(self):
        return OpenAPIParser()
    
    def test_parse_simple_spec(self, parser):
        """Test parsing simple OpenAPI spec"""
        title, version, operations = parser.parse_spec(SAMPLE_OPENAPI_JSON)
        
        assert title == "Pet Store API"
        assert version == "1.0.0"
        assert len(operations) == 3
    
    def test_parse_preserves_operation_details(self, parser):
        """Test that parsing preserves operation details"""
        title, version, operations = parser.parse_spec(SAMPLE_OPENAPI_JSON)
        
        # Check first operation
        op = next((o for o in operations if o.operation_id == "listPets"), None)
        assert op is not None
        assert op.path == "/pets"
        assert op.method == "get"
        assert "pets" in op.tags
        assert op.summary == "List all pets"
    
    def test_parse_extracts_parameters(self, parser):
        """Test that parameters are extracted"""
        title, version, operations = parser.parse_spec(SAMPLE_OPENAPI_JSON)
        
        op = next((o for o in operations if o.operation_id == "listPets"), None)
        assert "limit" in op.parameters
        assert op.parameters["limit"]["type"] == "integer"
    
    def test_parse_extracts_responses(self, parser):
        """Test that responses are extracted"""
        title, version, operations = parser.parse_spec(SAMPLE_OPENAPI_JSON)
        
        op = next((o for o in operations if o.operation_id == "listPets"), None)
        assert "200" in op.responses
        assert "default" in op.responses
    
    def test_parse_invalid_spec(self, parser):
        """Test parsing invalid spec raises error"""
        invalid_spec = {"invalid": "spec"}
        
        with pytest.raises(ValueError):
            parser.parse_spec(invalid_spec)
    
    def test_parse_swagger_format(self, parser):
        """Test parsing Swagger 2.0 format"""
        swagger_spec = {
            "swagger": "2.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {}
        }
        
        title, version, operations = parser.parse_spec(swagger_spec)
        assert title == "Test API"


class TestOpenAPILoader:
    """Tests for OpenAPILoader class"""
    
    @pytest.fixture
    def loader(self):
        return OpenAPILoader()
    
    @pytest.fixture
    def openapi_json_file(self):
        """Create a temporary OpenAPI JSON file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(SAMPLE_OPENAPI_JSON, f)
            f.flush()
            yield f.name
        
        Path(f.name).unlink()
    
    @pytest.fixture
    def openapi_yaml_file(self):
        """Create a temporary OpenAPI YAML file"""
        import yaml
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(SAMPLE_OPENAPI_JSON, f)
            f.flush()
            yield f.name
        
        Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_validate_json_file(self, loader):
        """Test validation of JSON files"""
        assert await loader.validate("spec.json")
        assert await loader.validate("spec.yaml")
        assert await loader.validate("spec.yml")
        assert not await loader.validate("spec.txt")
    
    @pytest.mark.asyncio
    async def test_load_json_spec(self, loader, openapi_json_file):
        """Test loading JSON OpenAPI spec"""
        doc = await loader.load(openapi_json_file)
        
        assert doc.content is not None
        assert doc.metadata.file_type == ".json"
        assert doc.metadata.api_title == "Pet Store API"
        assert doc.metadata.api_version == "1.0.0"
        assert doc.metadata.operation_count == 3
    
    @pytest.mark.asyncio
    async def test_load_yaml_spec(self, loader, openapi_yaml_file):
        """Test loading YAML OpenAPI spec"""
        doc = await loader.load(openapi_yaml_file)
        
        assert doc.content is not None
        assert doc.metadata.api_title == "Pet Store API"
        assert doc.metadata.operation_count == 3
    
    @pytest.mark.asyncio
    async def test_load_creates_chunks(self, loader, openapi_json_file):
        """Test that each operation becomes a chunk"""
        doc = await loader.load(openapi_json_file)
        
        assert doc.metadata.chunk_count == 3
        assert len(doc.chunks) == 3
        
        # Each chunk should be non-empty
        for chunk in doc.chunks:
            assert len(chunk.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_get_operations(self, loader, openapi_json_file):
        """Test retrieving parsed operations"""
        doc = await loader.load(openapi_json_file)
        operations = loader.get_operations()
        
        assert len(operations) == 3
        
        # Check operation details
        op_ids = [op.operation_id for op in operations]
        assert "listPets" in op_ids
        assert "createPets" in op_ids
        assert "showPetById" in op_ids
    
    @pytest.mark.asyncio
    async def test_get_operations_with_metadata(self, loader, openapi_json_file):
        """Test getting operations with metadata"""
        doc = await loader.load(openapi_json_file)
        ops_with_meta = loader.get_operations_with_metadata()
        
        assert len(ops_with_meta) == 3
        
        for op_meta in ops_with_meta:
            assert 'path' in op_meta
            assert 'method' in op_meta
            assert 'operation_id' in op_meta
            assert 'tags' in op_meta
            assert 'text' in op_meta
    
    @pytest.mark.asyncio
    async def test_get_operations_by_tag(self, loader, openapi_json_file):
        """Test filtering operations by tag"""
        doc = await loader.load(openapi_json_file)
        
        pet_ops = loader.get_operations_by_tag("pets")
        assert len(pet_ops) == 3
        
        # All should have 'pets' tag
        for op in pet_ops:
            assert "pets" in op.tags
    
    @pytest.mark.asyncio
    async def test_get_operation_by_id(self, loader, openapi_json_file):
        """Test retrieving specific operation by ID"""
        doc = await loader.load(openapi_json_file)
        
        op = loader.get_operation_by_id("listPets")
        assert op is not None
        assert op.path == "/pets"
        assert op.method == "get"
        
        # Non-existent operation
        op = loader.get_operation_by_id("nonExistent")
        assert op is None
    
    @pytest.mark.asyncio
    async def test_load_invalid_json(self, loader):
        """Test loading invalid JSON file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("{ invalid json }")
            f.flush()
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError):
                await loader.load(temp_file)
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, loader):
        """Test loading non-existent file"""
        with pytest.raises(FileNotFoundError):
            await loader.load("/nonexistent/spec.json")
    
    @pytest.mark.asyncio
    async def test_multiple_tags_per_operation(self):
        """Test operations with multiple tags"""
        loader = OpenAPILoader()
        
        # Create temporary file with multi-tag spec
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(SAMPLE_OPENAPI_MULTI_TAG, f)
            f.flush()
            temp_file = f.name
        
        try:
            doc = await loader.load(temp_file)
            
            # Find operations
            list_users = loader.get_operation_by_id("listUsers")
            assert "users" in list_users.tags
            assert "public" in list_users.tags
            
            create_user = loader.get_operation_by_id("createUser")
            assert "users" in create_user.tags
            assert "admin" in create_user.tags
        finally:
            Path(temp_file).unlink()
