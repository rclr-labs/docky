"""
OpenAPI/Swagger Specification Loader with Structured Parsing
"""
import logging
import json
from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass

import aiofiles
import yaml

from ingest.loader import BaseLoader, Document, DocumentMetadata


logger = logging.getLogger(__name__)


@dataclass
class OpenAPIOperation:
    """Represents an OpenAPI operation (endpoint)"""
    path: str
    method: str  # get, post, put, delete, patch, etc.
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    parameters: Dict[str, Any] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.parameters is None:
            self.parameters = {}
        if self.responses is None:
            self.responses = {}
    
    def to_markdown(self) -> str:
        """Convert operation to markdown format"""
        lines = []
        
        # Header
        method_upper = self.method.upper()
        lines.append(f"### {method_upper} {self.path}")
        
        if self.operation_id:
            lines.append(f"**OperationID:** `{self.operation_id}`")
        
        if self.summary:
            lines.append(f"**Summary:** {self.summary}")
        
        if self.description:
            lines.append(f"**Description:** {self.description}")
        
        if self.tags:
            tags_str = ", ".join(f"`{tag}`" for tag in self.tags)
            lines.append(f"**Tags:** {tags_str}")
        
        # Parameters
        if self.parameters:
            lines.append("**Parameters:**")
            for param_name, param_info in self.parameters.items():
                param_type = param_info.get('type', 'unknown')
                required = param_info.get('required', False)
                req_marker = "*(required)*" if required else "*(optional)*"
                lines.append(f"- `{param_name}` ({param_type}) {req_marker}")
                if param_info.get('description'):
                    lines.append(f"  - {param_info['description']}")
        
        # Request Body
        if self.request_body:
            lines.append("**Request Body:**")
            if isinstance(self.request_body, dict):
                content = self.request_body.get('content', {})
                for content_type in content.keys():
                    lines.append(f"- Content-Type: `{content_type}`")
        
        # Responses
        if self.responses:
            lines.append("**Responses:**")
            for status_code, response_info in self.responses.items():
                description = response_info.get('description', '')
                lines.append(f"- `{status_code}`: {description}")
        
        return '\n'.join(lines)
    
    def to_text(self) -> str:
        """Convert operation to plain text format"""
        lines = []
        
        lines.append(f"{self.method.upper()} {self.path}")
        
        if self.operation_id:
            lines.append(f"Operation ID: {self.operation_id}")
        
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        if self.tags:
            lines.append(f"Tags: {', '.join(self.tags)}")
        
        # Parameters
        if self.parameters:
            lines.append("Parameters:")
            for param_name, param_info in self.parameters.items():
                param_type = param_info.get('type', 'unknown')
                required = "required" if param_info.get('required', False) else "optional"
                lines.append(f"  {param_name} ({param_type}, {required})")
                if param_info.get('description'):
                    lines.append(f"    {param_info['description']}")
        
        # Responses
        if self.responses:
            lines.append("Responses:")
            for status_code, response_info in self.responses.items():
                description = response_info.get('description', '')
                lines.append(f"  {status_code}: {description}")
        
        return '\n'.join(lines)


class OpenAPIParser:
    """Parse OpenAPI/Swagger specifications"""
    
    SUPPORTED_VERSIONS = ['3.0.0', '3.0.1', '3.0.2', '3.0.3', '3.1.0']
    
    @staticmethod
    def parse_spec(spec: Dict[str, Any]) -> tuple[str, str, List[OpenAPIOperation]]:
        """
        Parse OpenAPI specification.
        
        Args:
            spec: OpenAPI specification dictionary
        
        Returns:
            Tuple of (title, version, list of operations)
        
        Raises:
            ValueError: If spec format is invalid
        """
        # Validate spec
        if 'openapi' not in spec and 'swagger' not in spec:
            raise ValueError("Invalid OpenAPI specification: missing 'openapi' or 'swagger' field")
        
        # Get metadata
        info = spec.get('info', {})
        title = info.get('title', 'Unknown API')
        version = info.get('version', '1.0.0')
        
        # Parse paths
        operations = []
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Skip if not an operation
                if method.startswith('x-') or method not in [
                    'get', 'post', 'put', 'delete', 'patch',
                    'options', 'head', 'trace'
                ]:
                    continue
                
                # Extract operation details
                operation_id = operation.get('operationId')
                summary = operation.get('summary')
                description = operation.get('description')
                tags = operation.get('tags', [])
                
                # Parse parameters
                parameters = {}
                param_list = operation.get('parameters', [])
                for param in param_list:
                    param_name = param.get('name')
                    if param_name:
                        param_info = {
                            'type': param.get('schema', {}).get('type', 'unknown'),
                            'required': param.get('required', False),
                            'description': param.get('description'),
                        }
                        parameters[param_name] = param_info
                
                # Parse request body
                request_body = operation.get('requestBody')
                
                # Parse responses
                responses = {}
                response_list = operation.get('responses', {})
                for status_code, response_info in response_list.items():
                    responses[status_code] = {
                        'description': response_info.get('description', ''),
                    }
                
                # Create operation
                op = OpenAPIOperation(
                    path=path,
                    method=method,
                    operation_id=operation_id,
                    summary=summary,
                    description=description,
                    tags=tags,
                    parameters=parameters,
                    request_body=request_body,
                    responses=responses,
                )
                
                operations.append(op)
        
        return title, version, operations


class OpenAPILoader(BaseLoader):
    """Loader for OpenAPI/Swagger specifications"""
    
    def __init__(self):
        """Initialize OpenAPI Loader"""
        self.parser = OpenAPIParser()
        self._last_operations = []
    
    async def load(self, file_path: str) -> Document:
        """
        Load and parse OpenAPI specification.
        
        Args:
            file_path: Path to OpenAPI spec file (JSON or YAML)
        
        Returns:
            Document object with content and chunks
        """
        logger.info(f"Loading OpenAPI specification: {file_path}")
        
        path = Path(file_path)
        
        # Read file
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Parse file based on extension
        file_ext = path.suffix.lower()
        try:
            if file_ext == '.json':
                spec = json.loads(content)
            elif file_ext in ['.yaml', '.yml']:
                spec = yaml.safe_load(content)
            else:
                # Try both formats
                try:
                    spec = json.loads(content)
                except json.JSONDecodeError:
                    spec = yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to parse OpenAPI spec: {e}")
            raise ValueError(f"Invalid OpenAPI file format: {e}")
        
        # Parse operations
        title, version, operations = self.parser.parse_spec(spec)
        logger.info(f"Parsed {len(operations)} operations from {file_path}")
        
        # Store operations for later access
        self._last_operations = operations
        
        # Create chunks - one per operation
        chunks = []
        for op in operations:
            chunks.append(op.to_text())
        
        # Prepare metadata
        file_size = path.stat().st_size
        metadata = DocumentMetadata(
            file_path=str(path),
            file_name=path.name,
            file_size=file_size,
            file_type=file_ext,
            api_title=title,
            api_version=version,
            operation_count=len(operations),
            chunk_count=len(chunks),
        )
        
        return Document(
            content=content,
            metadata=metadata,
            chunks=chunks
        )
    
    async def validate(self, file_path: str) -> bool:
        """Validate that file is an OpenAPI specification"""
        ext = Path(file_path).suffix.lower()
        return ext in ['.json', '.yaml', '.yml']
    
    def get_operations(self) -> List[OpenAPIOperation]:
        """
        Get parsed operations.
        
        Returns:
            List of OpenAPIOperation objects
        """
        return self._last_operations
    
    def get_operations_with_metadata(self) -> List[dict]:
        """
        Get operations with full metadata.
        
        Returns:
            List of operation dictionaries with metadata
        """
        return [
            {
                'path': op.path,
                'method': op.method,
                'operation_id': op.operation_id,
                'summary': op.summary,
                'description': op.description,
                'tags': op.tags,
                'parameter_count': len(op.parameters),
                'response_count': len(op.responses),
                'text': op.to_text(),
            }
            for op in self._last_operations
        ]
    
    def get_operations_by_tag(self, tag: str) -> List[OpenAPIOperation]:
        """
        Get operations filtered by tag.
        
        Args:
            tag: Tag to filter by
        
        Returns:
            List of operations with the specified tag
        """
        return [op for op in self._last_operations if tag in op.tags]
    
    def get_operation_by_id(self, operation_id: str) -> Optional[OpenAPIOperation]:
        """
        Get operation by operationId.
        
        Args:
            operation_id: The operationId to find
        
        Returns:
            Operation object or None if not found
        """
        for op in self._last_operations:
            if op.operation_id == operation_id:
                return op
        return None
