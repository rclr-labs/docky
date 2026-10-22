"""
Testes para document loaders
"""
import pytest
from pathlib import Path
from ingest.loader import (
    TextLoader,
    DocumentLoaderFactory,
    DocumentMetadata,
)

# MarkdownLoader mudou de módulo na refatoração que integrou os loaders ao
# DocumentLoaderFactory. O factory já importa daqui; este teste não acompanhou,
# e o ImportError abortava a COLETA do pytest — nenhum teste do repositório
# rodava, não só os deste arquivo.
from ingest.loaders.markdown_loader import MarkdownLoader


@pytest.fixture
def temp_text_file(tmp_path):
    """Criar arquivo de teste temporário"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Conteúdo de teste")
    return str(file_path)


@pytest.fixture
def temp_md_file(tmp_path):
    """Criar arquivo markdown de teste"""
    file_path = tmp_path / "test.md"
    file_path.write_text("# Título\n\nConteúdo markdown")
    return str(file_path)


@pytest.mark.asyncio
async def test_text_loader_load(temp_text_file):
    """Testar carregamento de arquivo texto"""
    loader = TextLoader()
    document = await loader.load(temp_text_file)
    
    assert document is not None
    assert document.content == "Conteúdo de teste"
    assert document.metadata.file_type == ".txt"


@pytest.mark.asyncio
async def test_text_loader_validate(temp_text_file):
    """Testar validação de arquivo texto"""
    loader = TextLoader()
    assert await loader.validate(temp_text_file) is True
    
    # Testar arquivo inválido
    assert await loader.validate("invalid.md") is False


@pytest.mark.asyncio
async def test_markdown_loader_load(temp_md_file):
    """Testar carregamento de arquivo markdown"""
    loader = MarkdownLoader()
    document = await loader.load(temp_md_file)
    
    assert document is not None
    assert "# Título" in document.content
    assert document.metadata.file_type == ".md"


def test_document_factory_get_loader():
    """Testar DocumentLoaderFactory"""
    txt_loader = DocumentLoaderFactory.get_loader("file.txt")
    assert isinstance(txt_loader, TextLoader)
    
    md_loader = DocumentLoaderFactory.get_loader("file.md")
    assert isinstance(md_loader, MarkdownLoader)
    
    unknown = DocumentLoaderFactory.get_loader("file.unknown")
    assert unknown is None


@pytest.mark.asyncio
async def test_document_factory_load_document(temp_text_file):
    """Testar carregamento via factory"""
    document = await DocumentLoaderFactory.load_document(temp_text_file)
    assert document is not None
    assert document.metadata.file_name == Path(temp_text_file).name
