"""
PPTX Loader: extrai texto dos slides e notas do apresentador de apresentações PowerPoint.

Cada slide vira um chunk proprio no formato:
    [Slide N - Titulo]
    <texto do slide>
    Notas do apresentador: <notas>

As notas do apresentador sao frequentemente o conteudo mais rico (a explicacao
completa que nao coube no slide), por isso sao sempre incluidas no chunk.
"""
import logging
from pathlib import Path
from typing import Optional

from ingest.loader import BaseLoader, Document, DocumentMetadata


logger = logging.getLogger(__name__)


class PPTXLoader(BaseLoader):
    """Loader para apresentacoes PowerPoint (.pptx)"""

    async def validate(self, file_path: str) -> bool:
        path = Path(file_path)
        return path.suffix.lower() == ".pptx" and path.is_file()

    async def load(self, file_path: str) -> Document:
        logger.info(f"Carregando PPTX: {file_path}")
        from pptx import Presentation  # import tardio: dependencia opcional

        path = Path(file_path)
        prs = Presentation(str(path))

        deck_title = self._extract_deck_title(prs) or path.stem
        chunks: list[str] = []
        full_parts: list[str] = []

        for idx, slide in enumerate(prs.slides, start=1):
            slide_title = self._slide_title(slide)
            body_text = self._slide_body_text(slide, slide_title)
            notes = self._slide_notes(slide)

            # Montar o chunk do slide com contexto embutido
            header = f"[{deck_title} - Slide {idx}" + (f": {slide_title}]" if slide_title else "]")
            parts = [header]
            if body_text:
                parts.append(body_text)
            if notes:
                parts.append(f"Notas do apresentador: {notes}")

            chunk = "\n".join(parts).strip()
            # Ignorar slides vazios (so layout/imagem sem texto nem notas)
            if body_text or notes:
                chunks.append(chunk)
                full_parts.append(chunk)

        content = "\n\n".join(full_parts)
        logger.info(f"  {len(chunks)} slides com conteudo extraidos")

        metadata = DocumentMetadata(
            file_path=str(path),
            file_name=path.name,
            file_size=path.stat().st_size,
            file_type=".pptx",
            deck_title=deck_title,
            slide_count=len(chunks),
        )
        return Document(content=content, metadata=metadata, chunks=chunks)

    # ----- helpers -----

    def _extract_deck_title(self, prs) -> Optional[str]:
        """Titulo do deck: titulo do primeiro slide, se houver"""
        try:
            first = prs.slides[0]
            return self._slide_title(first)
        except (IndexError, KeyError):
            return None

    def _slide_title(self, slide) -> Optional[str]:
        try:
            if slide.shapes.title and slide.shapes.title.text.strip():
                return slide.shapes.title.text.strip()
        except (AttributeError, KeyError):
            pass
        return None

    def _slide_body_text(self, slide, slide_title: Optional[str]) -> str:
        """Todo o texto do slide (exceto o titulo, ja usado no header)"""
        texts = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text_frame.text.strip()
            if not text or text == slide_title:
                continue
            texts.append(text)
        # Tabelas
        for shape in slide.shapes:
            if shape.has_table:
                for row in shape.table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        texts.append(" | ".join(cells))
        return "\n".join(texts)

    def _slide_notes(self, slide) -> str:
        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                return slide.notes_slide.notes_text_frame.text.strip()
        except (AttributeError, KeyError):
            pass
        return ""
