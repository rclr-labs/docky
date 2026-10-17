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


class MarkdownLoader(BaseLoader):
    """Loader para arquivos Markdown"""
    
    async def load(self, file_path: str) -> Document:
        """Carregar arquivo Markdown"""
        logger.info(f"Carregando arquivo Markdown: {file_path}")
        
        path = Path(file_path)
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        metadata = DocumentMetadata(
            file_path=str(path),
            file_name=path.name,
            file_size=path.stat().st_size,
            file_type=".md",
        )
        
        return Document(content=content, metadata=metadata)
    
    async def validate(self, file_path: str) -> bool:
        """Validar arquivo Markdown"""
        return Path(file_path).suffix.lower() == ".md"


class DocumentLoaderFactory:
    """Factory para criar loaders apropriados"""
    
    _loaders = {
        ".txt": TextLoader(),
        ".md": MarkdownLoader(),
        # TODO: Adicionar PDFLoader e DocXLoader
    }
    
    @classmethod
    def get_loader(cls, file_path: str) -> Optional[BaseLoader]:
        """Obter loader apropriado para o arquivo"""
        file_ext = Path(file_path).suffix.lower()
        return cls._loaders.get(file_ext)
    
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
