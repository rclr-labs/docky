"""
Ingest module for document loading and ingestion
"""
from ingest.loader import (
    Document,
    DocumentMetadata,
    BaseLoader,
    TextLoader,
    DocumentLoaderFactory,
)

# Lazy import to avoid circular dependencies
def get_ingestor():
    """Lazy import DocumentIngestor to avoid circular dependencies"""
    try:
        from ingest.ingestors import DocumentIngestor
        return DocumentIngestor
    except ImportError:
        return None

__all__ = [
    'Document',
    'DocumentMetadata', 
    'BaseLoader',
    'TextLoader',
    'DocumentLoaderFactory',
    'get_ingestor',
]
