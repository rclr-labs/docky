"""
Transcript Loader: transcricoes de video/audio com timestamps (Zoom, Meet, Whisper).

Formatos suportados:
  - .vtt (WebVTT - padrao das gravacoes em nuvem do Zoom e legendas do Meet/YouTube)
  - .srt (SubRip)

Os chunks sao janelas de fala agregadas (~TARGET_CHUNK_CHARS), cada uma prefixada
com o timestamp de inicio no formato [HH:MM:SS], permitindo que as respostas do
RAG citem o momento exato do video.
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiofiles

from ingest.loader import BaseLoader, Document, DocumentMetadata


logger = logging.getLogger(__name__)

# Tamanho alvo de cada chunk em caracteres (~250-300 tokens)
TARGET_CHUNK_CHARS = 1100
# Pausa (em segundos) entre cues que sugere troca de topico -> quebra de chunk
TOPIC_GAP_SECONDS = 8.0


@dataclass
class Cue:
    start: float  # segundos
    end: float
    text: str


def _ts_to_seconds(ts: str) -> float:
    """'HH:MM:SS.mmm' ou 'MM:SS.mmm' -> segundos"""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def _seconds_to_hms(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


_TIMING_RE = re.compile(
    r"(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}\s*-->\s*(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}"
)
# Zoom costuma prefixar o falante: "Nome Sobrenome: fala..."
_SPEAKER_RE = re.compile(r"^([A-Za-z\u00c0-\u00ff' .-]{2,40}):\s+")


class TranscriptLoader(BaseLoader):
    """Loader para transcricoes .vtt e .srt com timestamps"""

    SUPPORTED = {".vtt", ".srt"}

    async def validate(self, file_path: str) -> bool:
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED and path.is_file()

    async def load(self, file_path: str) -> Document:
        logger.info(f"Carregando transcricao: {file_path}")
        path = Path(file_path)

        async with aiofiles.open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw = await f.read()

        cues = self._parse_cues(raw)
        logger.info(f"  {len(cues)} cues parseados")

        chunks = self._build_chunks(cues, source_name=path.stem)
        logger.info(f"  {len(chunks)} chunks gerados")

        duration = cues[-1].end if cues else 0.0
        content = "\n\n".join(chunks)

        metadata = DocumentMetadata(
            file_path=str(path),
            file_name=path.name,
            file_size=path.stat().st_size,
            file_type=path.suffix.lower(),
            media_kind="video_transcript",
            duration_seconds=round(duration, 1),
            cue_count=len(cues),
        )
        return Document(content=content, metadata=metadata, chunks=chunks)

    # ----- parsing -----

    def _parse_cues(self, raw: str) -> list[Cue]:
        """Parser unico para VTT e SRT: procura linhas de timing 'X --> Y'"""
        cues: list[Cue] = []
        lines = raw.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            m = _TIMING_RE.search(line)
            if not m:
                i += 1
                continue
            start_s, end_s = [p.strip() for p in line.split("-->")[:2]]
            # VTT pode ter settings depois do timestamp final ("align:start position:0%")
            end_s = end_s.split()[0]
            start, end = _ts_to_seconds(start_s), _ts_to_seconds(end_s)

            # Coletar o texto ate a linha em branco
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            text = " ".join(text_lines).strip()
            # Remover tags de voz do VTT (<v Nome>) mantendo o nome do falante
            text = re.sub(r"<v\s+([^>]+)>", r"\1: ", text)
            text = re.sub(r"</?[^>]+>", "", text)
            if text:
                cues.append(Cue(start=start, end=end, text=text))
        return cues

    def _build_chunks(self, cues: list[Cue], source_name: str) -> list[str]:
        """Agregar cues em janelas de ~TARGET_CHUNK_CHARS, quebrando em pausas longas."""
        if not cues:
            return []

        chunks: list[str] = []
        buf: list[str] = []
        buf_start: float = cues[0].start
        buf_len = 0
        prev_end: Optional[float] = None
        last_speaker: Optional[str] = None

        def flush():
            nonlocal buf, buf_len, last_speaker
            if buf:
                body = " ".join(buf).strip()
                chunks.append(f"[{source_name} @ {_seconds_to_hms(buf_start)}] {body}")
            buf = []
            buf_len = 0
            last_speaker = None

        for cue in cues:
            gap = (cue.start - prev_end) if prev_end is not None else 0.0
            if buf and (buf_len >= TARGET_CHUNK_CHARS or gap >= TOPIC_GAP_SECONDS):
                flush()
                buf_start = cue.start

            text = cue.text
            # Evitar repetir o nome do falante a cada cue consecutivo da mesma pessoa
            m = _SPEAKER_RE.match(text)
            if m:
                speaker = m.group(1)
                if speaker == last_speaker:
                    text = text[m.end():]
                else:
                    last_speaker = speaker

            buf.append(text)
            buf_len += len(text) + 1
            prev_end = cue.end

        flush()
        return chunks
