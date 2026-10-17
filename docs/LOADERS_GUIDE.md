# Document Loaders - Reference Guide

## Overview

The document loader system provides a pluggable architecture for loading and chunking various document formats into the RAG pipeline.

---

## Available Loaders

### 1. TextLoader
**File Extensions:** `.txt`

Simple text file loader. Returns entire file as single chunk with basic metadata.

```python
from ingest.loader import DocumentLoaderFactory

doc = await DocumentLoaderFactory.load_document("document.txt")
print(doc.content)  # Full file content
print(doc.chunks)   # Single chunk containing all content
```

---

### 2. MarkdownLoader
**File Extensions:** `.md`  
**Location:** `ingest/loaders/markdown_loader.py`

Structure-aware markdown parser that preserves document hierarchy and creates overlapping chunks.

#### Key Features
- **Structure Preservation:** Tracks heading hierarchy (H1 > H2 > H3)
- **Smart Chunking:** Token-based (default 512 tokens) with overlap (default 50)
- **Rich Metadata:** Includes section path, heading levels, token counts, line numbers

#### Configuration
```python
from ingest.loaders.markdown_loader import MarkdownLoader

# Custom chunk size
loader = MarkdownLoader(chunk_size=256, overlap=25)
doc = await loader.load("document.md")
```

#### Metadata Available
```python
# Via factory
doc = await DocumentLoaderFactory.load_document("guide.md")
print(doc.metadata.chunk_count)      # Number of chunks
print(doc.metadata.section_count)    # Number of sections
print(doc.metadata.chunk_size)       # Configured chunk size

# Detailed chunk metadata
loader = DocumentLoaderFactory.get_loader("guide.md")
chunks_meta = loader.get_chunks_with_metadata()
for chunk in chunks_meta:
    print(chunk['section'])           # "Getting Started > Installation"
    print(chunk['heading_hierarchy']) # {'h1': '...', 'h2': '...'}
    print(chunk['token_count'])       # Estimated token count
    print(chunk['start_line'])        # Line number in original file
```

#### Example
```
Input Markdown:
# Introduction
Content here
## Installation
More content

Output:
- Chunk 1: "# Introduction\nContent here"
  Section: "Introduction"
  Hierarchy: {h1: "Introduction"}
  
- Chunk 2: "## Installation\nMore content"
  Section: "Introduction > Installation"
  Hierarchy: {h1: "Introduction", h2: "Installation"}
```

---

### 3. OpenAPILoader
**File Extensions:** `.json`, `.yaml`, `.yml`  
**Location:** `ingest/loaders/openapi_loader.py`

Parses OpenAPI 3.0+ and Swagger 2.0 specifications, extracting individual operations as chunks.

#### Key Features
- **Multi-Format Support:** JSON and YAML parsing
- **Full Spec Support:** OpenAPI 3.0+ and Swagger 2.0
- **Operation Extraction:** Each endpoint becomes a chunk
- **Rich Metadata:** Paths, methods, operationIds, tags, parameters, responses

#### Configuration
```python
from ingest.loaders.openapi_loader import OpenAPILoader

loader = OpenAPILoader()
doc = await loader.load("api-spec.json")
```

#### Metadata Available
```python
# Via factory
doc = await DocumentLoaderFactory.load_document("api-spec.json")
print(doc.metadata.api_title)         # "Pet Store API"
print(doc.metadata.api_version)       # "1.0.0"
print(doc.metadata.operation_count)   # 3
print(doc.metadata.chunk_count)       # 3 (one per operation)

# Get operations
loader = DocumentLoaderFactory.get_loader("api-spec.json")
operations = loader.get_operations()  # List of OpenAPIOperation objects

# Get operations with metadata
ops_meta = loader.get_operations_with_metadata()
for op in ops_meta:
    print(op['path'])                 # "/pets"
    print(op['method'])               # "get"
    print(op['operation_id'])         # "listPets"
    print(op['tags'])                 # ["pets"]
    print(op['parameter_count'])      # 1
    print(op['response_count'])       # 2
```

#### Query Methods
```python
loader = DocumentLoaderFactory.get_loader("api-spec.json")

# Filter by tag
pet_ops = loader.get_operations_by_tag("pets")
for op in pet_ops:
    print(op.path, op.method)

# Get specific operation
op = loader.get_operation_by_id("listPets")
if op:
    print(f"{op.method.upper()} {op.path}")
    print(op.summary)
    print(op.description)
```

#### Example
```
Input OpenAPI:
paths:
  /pets:
    get:
      operationId: listPets
      parameters:
        - name: limit
          type: integer
      responses:
        200:
          description: Success

Output:
- Chunk 1: "GET /pets\nOperation ID: listPets\n..."
  Path: "/pets"
  Method: "get"
  Tags: []
  Parameters: {"limit": {"type": "integer", ...}}
```

---

## DocumentLoaderFactory

Central factory for loader management with auto-detection and registration.

### Basic Usage
```python
from ingest.loader import DocumentLoaderFactory

# Auto-detect and load
doc = await DocumentLoaderFactory.load_document("file.md")

# Check format support
if DocumentLoaderFactory.supports_format(".md"):
    # Load markdown
    pass

# Get all supported formats
formats = DocumentLoaderFactory.get_supported_formats()
# ['.txt', '.md', '.json', '.yaml', '.yml']

# Get specific loader
loader = DocumentLoaderFactory.get_loader("file.md")
```

### Custom Loader Registration
```python
from ingest.loader import BaseLoader, Document, DocumentMetadata

class PDFLoader(BaseLoader):
    async def load(self, file_path: str) -> Document:
        # Implementation
        pass
    
    async def validate(self, file_path: str) -> bool:
        return file_path.endswith('.pdf')

# Register
pdf_loader = PDFLoader()
DocumentLoaderFactory.register_loader(".pdf", pdf_loader)

# Now available
doc = await DocumentLoaderFactory.load_document("document.pdf")
```

---

## Document Structure

### Document Object
```python
class Document:
    content: str                          # Full document content
    metadata: DocumentMetadata            # File metadata
    chunks: List[str]                     # Document chunks
```

### DocumentMetadata
```python
class DocumentMetadata:
    file_path: str                        # Full file path
    file_name: str                        # File name
    file_size: int                        # File size in bytes
    file_type: str                        # Extension (.md, .json, etc.)
    source_url: Optional[str]             # Optional source URL
    **kwargs                              # Format-specific metadata
```

### Format-Specific Metadata

**Markdown:**
- `chunk_count` - Total number of chunks
- `section_count` - Total number of sections
- `chunk_size` - Configured chunk size in tokens
- `overlap` - Configured overlap in tokens

**OpenAPI:**
- `api_title` - API title from spec
- `api_version` - API version
- `operation_count` - Total operations
- `chunk_count` - Total chunks (equals operation count)

---

## Error Handling

```python
from ingest.loader import DocumentLoaderFactory
import logging

logger = logging.getLogger(__name__)

async def load_safely(file_path: str):
    try:
        doc = await DocumentLoaderFactory.load_document(file_path)
        if doc is None:
            logger.warning(f"Unsupported format: {file_path}")
            return None
        return doc
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except ValueError as e:
        logger.error(f"Invalid file format: {e}")
        return None
```

---

## Performance Considerations

### Markdown Loader
- **Token Estimation:** words × 1.3 (approximate)
- **Chunk Size:** Default 512 tokens ≈ 400 words
- **Overlap:** Default 50 tokens ≈ 40 words
- **Memory:** Full file loaded into memory

### OpenAPI Loader
- **Parsing:** JSON/YAML parsing overhead
- **Chunking:** One chunk per operation (linear scaling)
- **Memory:** Spec loaded into memory

### Optimization Tips
```python
# For large markdown files, increase chunk size
loader = MarkdownLoader(chunk_size=1024, overlap=100)

# Process in batches
docs = []
for file_path in file_list:
    doc = await DocumentLoaderFactory.load_document(file_path)
    if doc:
        docs.append(doc)
```

---

## Testing

Run all loader tests:
```bash
pytest tests/unit/test_markdown_loader.py -v
pytest tests/unit/test_openapi_loader.py -v
pytest tests/integration/test_loader_factory.py -v
```

Test coverage:
- Markdown Loader: 23 tests (99% coverage)
- OpenAPI Loader: 20 tests (77% coverage)
- Factory Integration: 13 tests

---

## Roadmap

Future loaders planned:
- PDF Loader (PDFLoader)
- DOCX Loader (DocxLoader)
- HTML Loader (HTMLLoader)
- RST Loader (RestructuredTextLoader)

Custom chunking strategies:
- Token-aware chunking
- Semantic chunking
- Sliding window strategies

---

## Support

For issues or questions:
1. Check test files for usage examples
2. Review inline code documentation
3. Refer to this guide's examples section
