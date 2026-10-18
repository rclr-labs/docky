"""
Document loaders para diferentes formatos de arquivo
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import aiofiles


logger = logging.getLogger(__name__)


class DocumentMetadata:
    """Metadados de um documento"""
    
    def __init__(
        self,
        file_path: str,
        file_name: str,
        file_size: int,
        file_type: str,
        source_url: Optional[str] = None,
        **kwargs
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.file_type = file_type
        self.source_url = source_url
        self.custom_metadata = kwargs
        # Also set kwargs as attributes for easy access
        for key, value in kwargs.items():
            setattr(self, key, value)


class Document:
    """Documento processado"""
    
    def __init__(
        self,
        content: str,
        metadata: DocumentMetadata,
        chunks: Optional[list[str]] = None,
    ):
        self.content = content
        self.metadata = metadata
        self.chunks = chunks or []


class BaseLoader(ABC):
    """Classe base para document loaders"""
    
    @abstractmethod
    async def load(self, file_path: str) -> Document:
        """Carregar documento do arquivo"""
        pass
    
    @abstractmethod
    async def validate(self, file_path: str) -> bool:
        """Validar se o arquivo pode ser processado"""
        pass


class TextLoader(BaseLoader):
    """Loader para arquivos de texto simples"""
    
    async def load(self, file_path: str) -> Document:
        """Carregar arquivo de texto"""
        logger.info(f"Carregando arquivo de texto: {file_path}")
        
        path = Path(file_path)
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        metadata = DocumentMetadata(
            file_path=str(path),
            file_name=path.name,
            file_size=path.stat().st_size,
            file_type=".txt",
        )
        
        return Document(content=content, metadata=metadata)
    
    async def validate(self, file_path: str) -> bool:
        """Validar arquivo de texto"""
        return Path(file_path).suffix.lower() == ".txt"


class DocumentLoaderFactory:
    """Factory para criar loaders apropriados"""
    
    _loaders = None
    _initialized = False
    
    @classmethod
    def _initialize_loaders(cls):
        """Initialize loaders lazily to avoid circular imports"""
        if cls._initialized:
            return
        
        cls._loaders = {
            ".txt": TextLoader(),
        }
        
        # Try to import and register markdown loader
        try:
            from ingest.loaders.markdown_loader import MarkdownLoader
            cls._loaders[".md"] = MarkdownLoader()
            logger.info("Registered MarkdownLoader")
        except ImportError as e:
            logger.debug(f"MarkdownLoader not available: {e}")
        
        # Try to import and register OpenAPI loader
        try:
            from ingest.loaders.openapi_loader import OpenAPILoader
            cls._loaders[".json"] = OpenAPILoader()
            cls._loaders[".yaml"] = OpenAPILoader()
            cls._loaders[".yml"] = OpenAPILoader()
            logger.info("Registered OpenAPILoader")
        except ImportError as e:
            logger.debug(f"OpenAPILoader not available: {e}")
        
        # Try to import and register PPTX loader (requer python-pptx)
        try:
            from ingest.loaders.pptx_loader import PPTXLoader
            cls._loaders[".pptx"] = PPTXLoader()
            logger.info("Registered PPTXLoader")
        except ImportError as e:
            logger.debug(f"PPTXLoader not available: {e}")
        
        # Try to import and register transcript loader (VTT/SRT de Zoom/Meet/Whisper)
        try:
            from ingest.loaders.transcript_loader import TranscriptLoader
            cls._loaders[".vtt"] = TranscriptLoader()
            cls._loaders[".srt"] = TranscriptLoader()
            logger.info("Registered TranscriptLoader")
        except ImportError as e:
            logger.debug(f"TranscriptLoader not available: {e}")
        
        cls._initialized = True
    
    @classmethod
    def get_loader(cls, file_path: str) -> Optional[BaseLoader]:
        """Obter loader apropriado para o arquivo"""
        cls._initialize_loaders()
        file_ext = Path(file_path).suffix.lower()
        return cls._loaders.get(file_ext)
    
    @classmethod
    def register_loader(cls, file_ext: str, loader: BaseLoader):
        """Registrar novo loader para extensão"""
        cls._initialize_loaders()
        if not file_ext.startswith('.'):
            file_ext = '.' + file_ext
        cls._loaders[file_ext] = loader
        logger.info(f"Registered loader for {file_ext}: {loader.__class__.__name__}")
    
    @classmethod
    async def load_document(cls, file_path: str) -> Optional[Document]:
        """Carregar documento com loader apropriado"""
        loader = cls.get_loader(file_path)
        if not loader:
            logger.warning(f"Nenhum loader disponível para: {file_path}")
            return None
        
        if not await loader.validate(file_path):
            logger.warning(f"Arquivo inválido: {file_path}")
            return None
        
        return await loader.load(file_path)
    
    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Obter lista de formatos suportados"""
        cls._initialize_loaders()
        return list(cls._loaders.keys())
    
    @classmethod
    def supports_format(cls, file_ext: str) -> bool:
        """Verificar se formato é suportado"""
        cls._initialize_loaders()
        if not file_ext.startswith('.'):
            file_ext = '.' + file_ext
        return file_ext in cls._loaders
