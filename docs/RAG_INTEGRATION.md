# RAG Integration - Document Ingestor

## Architecture

The DocumentIngestor integrates the loader framework with the RAG pipeline:

```
┌─────────────────┐
│  Document Files │
│  (various types)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  DocumentLoaderFactory      │
│  (format detection)         │
├─────────────────────────────┤
│ - TextLoader                │
│ - MarkdownLoader            │
│ - OpenAPILoader             │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  DocumentIngestor           │
│  (chunking + metadata)      │
├─────────────────────────────┤
│ - Pre-processed chunks      │
│ - Metadata extraction       │
│ - Error handling            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SearchService              │
│  (embeddings + Qdrant)      │
├─────────────────────────────┤
│ - Embed chunks              │
│ - Index in Qdrant           │
│ - Re-ranking ready          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Vector DB (Qdrant)         │
│  (semantic search)          │
└─────────────────────────────┘
```

## DocumentIngestor API

### Initialization

```python
from ingest.ingestors import DocumentIngestor
from api.search import SearchService

search_service = SearchService()
ingestor = DocumentIngestor(search_service)
```

### Single Document Ingestion

```python
result = await ingestor.ingest(
    file_path="docs/guide.md",
    doc_id=None,           # Auto-generated if None
    chunk_size=512,        # Tokens
    chunk_overlap=50,      # Tokens
)

# IngestResult object
print(result.doc_id)           # Document ID
print(result.file_name)        # File name
print(result.format)           # File type (.md, .json, etc)
print(result.chunks_indexed)   # Number of chunks
print(result.status)           # "success" or "error"
print(result.error_message)    # Error details if failed
```

### Batch Ingestion

```python
results = await ingestor.ingest_batch(
    file_paths=[
        "docs/guide.md",
        "docs/api.json",
        "README.txt",
    ],
    chunk_size=512,
    chunk_overlap=50,
)

# Results is a list of IngestResult objects
for result in results:
    if result.status == "success":
        print(f"✅ {result.file_name}: {result.chunks_indexed} chunks")
    else:
        print(f"❌ {result.file_name}: {result.error_message}")
```

### System Preparation

```python
# Ensure Qdrant collection exists
ready = await ingestor.ensure_ready()
if not ready:
    print("Failed to prepare system")

# Get supported formats
formats = ingestor.get_supported_formats()
print(formats)  # ['.txt', '.md', '.json', '.yaml', '.yml']
```

## Integration Example

```python
import asyncio
from ingest.ingestors import DocumentIngestor
from api.search import SearchService
from api.rag import RAGService

async def setup_rag_with_documents():
    # Initialize services
    search_service = SearchService()
    ingestor = DocumentIngestor(search_service)
    rag_service = RAGService(search_service)
    
    # Ensure infrastructure is ready
    await ingestor.ensure_ready()
    
    # Ingest documents
    print("Ingesting documents...")
    results = await ingestor.ingest_batch([
        "docs/overview.md",
        "docs/api/endpoints.json",
        "docs/guide.md",
    ])
    
    # Report results
    successful = sum(1 for r in results if r.status == "success")
    total_chunks = sum(r.chunks_indexed for r in results)
    print(f"Ingested {successful}/{len(results)} documents")
    print(f"Total chunks indexed: {total_chunks}")
    
    # Now RAG is ready to use
    response = await rag_service.query("How do I use the API?")
    print(response.answer)
    
    # Cleanup
    await search_service.close()

asyncio.run(setup_rag_with_documents())
```

## Format-Specific Behavior

### Text Files (.txt)

- **Chunking**: Generic by character count
- **Metadata**: File info only
- **Use case**: Plain text documentation, logs, notes

```
Input:  "Long text content..."
Output: Multiple fixed-size chunks
```

### Markdown Files (.md)

- **Chunking**: Structure-aware by heading hierarchy
- **Metadata**: Includes section path, heading levels
- **Use case**: Documentation with hierarchical structure

```
Input:
# Main Section
Content...
## Subsection
More content...

Output:
- Chunk 1: "# Main Section\nContent..."
  Section: "Main Section"
  
- Chunk 2: "## Subsection\nMore content..."
  Section: "Main Section > Subsection"
```

### OpenAPI/Swagger Files (.json, .yaml)

- **Chunking**: One chunk per operation
- **Metadata**: Path, method, operationId, tags, parameters
- **Use case**: API documentation

```
Input: OpenAPI spec with 5 endpoints
Output: 5 chunks (one per endpoint)

Each chunk includes:
- Operation details
- Parameters
- Responses
- Tags
```

## Metadata Structure

All chunks stored in Qdrant include:

```python
{
    # Standard metadata
    "file_name": "guide.md",
    "file_path": "/path/to/guide.md",
    "file_type": ".md",
    "file_size": 2048,
    
    # Chunk info
    "doc_id": "abc-123-def",
    "chunk_index": 0,
    "chunk_text": "Content of chunk...",
    
    # Format-specific metadata
    # (for Markdown)
    "section": "Title > Subsection",
    "heading_hierarchy": {"h1": "Title", "h2": "Subsection"},
    
    # (for OpenAPI)
    "api_title": "Pet Store API",
    "api_version": "1.0.0",
    "path": "/pets",
    "method": "get",
    "operation_id": "listPets",
    "tags": ["pets"],
}
```

## Error Handling

The ingestor provides detailed error information:

```python
result = await ingestor.ingest("document.pdf")

if result.status == "error":
    print(f"Error: {result.error_message}")
    # Possible errors:
    # - "Formato não suportado ou arquivo inválido"
    # - "Nenhum chunk foi indexado"
    # - "qdrant-client não instalado"
    # - Custom error messages
```

## Performance Considerations

### Chunking Strategy

- **Small chunks (256)**: More chunks, better context isolation
- **Medium chunks (512)**: Balanced (default)
- **Large chunks (1024)**: Fewer chunks, more context

### Overlap

- **Minimal (25)**: Less redundancy, smaller index
- **Medium (50)**: Balanced (default)
- **Large (100)**: More context preservation

### Batch Processing

```python
# For large batches, process in sub-batches
documents = ["doc1.md", "doc2.md", ..., "doc100.md"]

for i in range(0, len(documents), 10):
    batch = documents[i:i+10]
    results = await ingestor.ingest_batch(batch)
    print(f"Processed batch {i//10 + 1}")
```

## Integration with RAG Pipeline

The DocumentIngestor connects to the full RAG pipeline:

```
Documents → Ingestor → Qdrant → SearchService → RAGService
                           ↓
                    Vector Embeddings
                    (Semantic Search)
                           ↓
                      ReRanking
                           ↓
                      LLM Prompt
                           ↓
                      Response
```

### Complete RAG Flow

1. **Ingestion**: DocumentIngestor loads and chunks documents
2. **Embedding**: SearchService generates embeddings
3. **Indexing**: Chunks are stored in Qdrant with metadata
4. **Retrieval**: User query is embedded and searched
5. **Ranking**: Results are re-ranked by relevance
6. **Generation**: LLM generates answer from top results

## Configuration

### Default Settings

```python
# In api/config.py
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION_NAME = "documents"
QDRANT_API_KEY = None  # Optional
```

### Customization

```python
# Custom chunk configuration
result = await ingestor.ingest(
    file_path="document.md",
    chunk_size=1024,        # Larger chunks
    chunk_overlap=200,      # More overlap
)

# Custom document ID
result = await ingestor.ingest(
    file_path="document.md",
    doc_id="my-custom-id",  # Custom ID
)

# Batch with custom settings
results = await ingestor.ingest_batch(
    file_paths=files,
    chunk_size=256,         # Smaller chunks
    chunk_overlap=25,       # Less overlap
)
```

## Testing

Integration tests verify:
- Single document ingestion
- Batch ingestion
- Multiple file formats
- Error handling
- Custom IDs
- Metadata preservation

```bash
pytest tests/integration/test_ingestor.py -v
```

## Future Enhancements

- PDF loader with layout awareness
- DOCX loader with formatting preservation
- Streaming for large files
- Custom chunking strategies
- Semantic similarity deduplication
- Document versioning
- Metadata tagging system
