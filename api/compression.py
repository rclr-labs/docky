"""
Módulo de compressão extrativa de contexto para reduzir tokens
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class CompressionResult:
    """Resultado da compressão"""
    
    def __init__(
        self,
        original_text: str,
        compressed_text: str,
        compression_ratio: float,
        method: str,
        tokens_saved: int,
    ):
        self.original_text = original_text
        self.compressed_text = compressed_text
        self.compression_ratio = compression_ratio
        self.method = method
        self.tokens_saved = tokens_saved


class BaseCompressor(ABC):
    """Classe base para compressores"""
    
    @abstractmethod
    def compress(self, text: str, max_length: Optional[int] = None) -> CompressionResult:
        """Comprimir texto"""
        pass


class SentenceCompressor(BaseCompressor):
    """Compressor baseado em relevância de sentenças"""
    
    def __init__(self, threshold: float = 0.3):
        """
        Inicializar compressor
        
        Args:
            threshold: Score mínimo para manter sentença (0-1)
        """
        self.threshold = threshold
    
    def compress(self, text: str, max_length: Optional[int] = None) -> CompressionResult:
        """
        Comprimir mantendo sentenças mais relevantes
        
        Args:
            text: Texto a comprimir
            max_length: Comprimento máximo após compressão
            
        Returns:
            CompressionResult
        """
        if not text or len(text.strip()) == 0:
            return CompressionResult(
                original_text=text,
                compressed_text="",
                compression_ratio=0.0,
                method="sentence",
                tokens_saved=0,
            )
        
        # Dividir em sentenças
        sentences = self._split_sentences(text)
        
        if not sentences:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                compression_ratio=0.0,
                method="sentence",
                tokens_saved=0,
            )
        
        # Calcular scores de relevância
        scores = self._score_sentences(sentences)
        
        # Manter sentenças com score > threshold
        compressed_sentences = [
            s for s, score in zip(sentences, scores)
            if score >= self.threshold
        ]
        
        # Se nenhuma sentença passou, manter a primeira
        if not compressed_sentences:
            compressed_sentences = [sentences[0]]
        
        compressed = " ".join(compressed_sentences)
        
        # Aplicar max_length se especificado
        if max_length and len(compressed) > max_length:
            compressed = compressed[:max_length].rsplit(" ", 1)[0] + "..."
        
        # Calcular métricas
        original_tokens = len(text) // 4
        compressed_tokens = len(compressed) // 4
        tokens_saved = original_tokens - compressed_tokens
        compression_ratio = (1 - len(compressed) / len(text)) * 100
        
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            compression_ratio=compression_ratio,
            method="sentence",
            tokens_saved=tokens_saved,
        )
    
    def _split_sentences(self, text: str) -> list[str]:
        """Dividir texto em sentenças"""
        # Regex para dividir em pontos, exclamação, interrogação
        sentences = re.split(r'(?<=[.!?])s+', text)
        # Limpar espaços em branco
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _score_sentences(self, sentences: list[str]) -> list[float]:
        """
        Score cada sentença por relevância
        Heurística: comprimento, posição, palavras-chave
        """
        scores = []
        
        for i, sentence in enumerate(sentences):
            # Sentença muito curta = baixo score
            if len(sentence) < 10:
                scores.append(0.1)
                continue
            
            # Sentenças no início e final têm score mais alto
            position_boost = 0.2 if (i == 0 or i == len(sentences) - 1) else 0.0
            
            # Score baseado em comprimento (50-200 caracteres é ideal)
            length_score = min(1.0, len(sentence) / 150)
            
            # Palavras-chave
            keywords = ["important", "critical", "key", "must", "essential",
                       "significan", "require", "define", "explain"]
            keyword_score = sum(1 for kw in keywords if kw.lower() in sentence.lower())
            keyword_score = min(1.0, keyword_score * 0.1)
            
            # Score final
            score = (length_score * 0.5 + keyword_score * 0.3 + position_boost * 0.2)
            scores.append(score)
        
        return scores


class KeywordCompressor(BaseCompressor):
    """Compressor baseado em keywords"""
    
    def __init__(self, keywords: Optional[list[str]] = None):
        """
        Inicializar compressor com keywords
        
        Args:
            keywords: Lista de keywords para manter
        """
        self.keywords = keywords or []
    
    def compress(self, text: str, max_length: Optional[int] = None) -> CompressionResult:
        """
        Comprimir mantendo apenas sentenças com keywords
        
        Args:
            text: Texto a comprimir
            max_length: Comprimento máximo após compressão
            
        Returns:
            CompressionResult
        """
        if not text or not self.keywords:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                compression_ratio=0.0,
                method="keyword",
                tokens_saved=0,
            )
        
        # Dividir em sentenças
        sentences = re.split(r'(?<=[.!?])s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Manter sentenças que contêm keywords
        compressed_sentences = [
            s for s in sentences
            if any(kw.lower() in s.lower() for kw in self.keywords)
        ]
        
        # Se nenhuma sentença tem keyword, manter a primeira
        if not compressed_sentences:
            compressed_sentences = sentences[:1] if sentences else []
        
        compressed = " ".join(compressed_sentences)
        
        # Aplicar max_length
        if max_length and len(compressed) > max_length:
            compressed = compressed[:max_length].rsplit(" ", 1)[0] + "..."
        
        # Calcular métricas
        original_tokens = len(text) // 4
        compressed_tokens = len(compressed) // 4
        tokens_saved = original_tokens - compressed_tokens
        compression_ratio = (1 - len(compressed) / len(text)) * 100 if text else 0
        
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            compression_ratio=compression_ratio,
            method="keyword",
            tokens_saved=tokens_saved,
        )


class LengthCompressor(BaseCompressor):
    """Compressor simples por comprimento máximo"""
    
    def compress(self, text: str, max_length: Optional[int] = None) -> CompressionResult:
        """
        Comprimir truncando ao comprimento máximo
        
        Args:
            text: Texto a comprimir
            max_length: Comprimento máximo (default: 300)
            
        Returns:
            CompressionResult
        """
        max_length = max_length or 300
        
        if len(text) <= max_length:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                compression_ratio=0.0,
                method="length",
                tokens_saved=0,
            )
        
        # Truncar respeitando limites de palavra
        compressed = text[:max_length]
        last_space = compressed.rfind(" ")
        
        if last_space > max_length * 0.7:
            compressed = compressed[:last_space]
        
        compressed = compressed.rstrip() + "..."
        
        # Calcular métricas
        original_tokens = len(text) // 4
        compressed_tokens = len(compressed) // 4
        tokens_saved = original_tokens - compressed_tokens
        compression_ratio = (1 - len(compressed) / len(text)) * 100
        
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            compression_ratio=compression_ratio,
            method="length",
            tokens_saved=tokens_saved,
        )


class ParagraphCompressor(BaseCompressor):
    """Compressor mantendo apenas parágrafos principais"""
    
    def __init__(self, keep_paragraphs: int = 2):
        """
        Inicializar compressor
        
        Args:
            keep_paragraphs: Número de parágrafos a manter
        """
        self.keep_paragraphs = keep_paragraphs
    
    def compress(self, text: str, max_length: Optional[int] = None) -> CompressionResult:
        """
        Comprimir mantendo primeiros N parágrafos
        
        Args:
            text: Texto a comprimir
            max_length: Comprimento máximo após compressão
            
        Returns:
            CompressionResult
        """
        if not text:
            return CompressionResult(
                original_text=text,
                compressed_text="",
                compression_ratio=0.0,
                method="paragraph",
                tokens_saved=0,
            )
        
        # Dividir em parágrafos (linhas vazias)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Manter primeiros N parágrafos
        kept = paragraphs[:self.keep_paragraphs]
        compressed = "\n\n".join(kept)
        
        # Aplicar max_length
        if max_length and len(compressed) > max_length:
            compressed = compressed[:max_length].rsplit(" ", 1)[0] + "..."
        
        # Calcular métricas
        original_tokens = len(text) // 4
        compressed_tokens = len(compressed) // 4
        tokens_saved = original_tokens - compressed_tokens
        compression_ratio = (1 - len(compressed) / len(text)) * 100 if text else 0
        
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            compression_ratio=compression_ratio,
            method="paragraph",
            tokens_saved=tokens_saved,
        )


class CompressionService:
    """Serviço de compressão com múltiplas estratégias"""
    
    def __init__(self):
        """Inicializar serviço com todos os compressores"""
        self.compressors = {
            "sentence": SentenceCompressor(threshold=0.3),
            "keyword": KeywordCompressor(),
            "length": LengthCompressor(),
            "paragraph": ParagraphCompressor(keep_paragraphs=2),
        }
        
        logger.info("✅ CompressionService inicializado")
    
    def compress(
        self,
        text: str,
        method: str = "sentence",
        max_length: Optional[int] = None,
        **kwargs
    ) -> CompressionResult:
        """
        Comprimir texto usando método especificado
        
        Args:
            text: Texto a comprimir
            method: Método de compressão (sentence, keyword, length, paragraph)
            max_length: Comprimento máximo após compressão
            **kwargs: Argumentos adicionais para o compressor
            
        Returns:
            CompressionResult
        """
        if method not in self.compressors:
            logger.warning(f"Método desconhecido: {method}, usando 'sentence'")
            method = "sentence"
        
        compressor = self.compressors[method]
        result = compressor.compress(text, max_length=max_length)
        
        logger.debug(
            f"Compressão com {method}: "
            f"{len(text)} → {len(result.compressed_text)} chars "
            f"({result.compression_ratio:.1f}% redução, {result.tokens_saved} tokens saved)"
        )
        
        return result
    
    def compress_chunks(
        self,
        chunks: list[str],
        method: str = "sentence",
        max_chunk_length: int = 300,
    ) -> list[CompressionResult]:
        """
        Comprimir múltiplos chunks
        
        Args:
            chunks: Lista de textos a comprimir
            method: Método de compressão
            max_chunk_length: Comprimento máximo por chunk
            
        Returns:
            Lista de CompressionResult
        """
        results = []
        
        for chunk in chunks:
            result = self.compress(
                text=chunk,
                method=method,
                max_length=max_chunk_length,
            )
            results.append(result)
        
        total_original = sum(len(r.original_text) for r in results)
        total_compressed = sum(len(r.compressed_text) for r in results)
        total_saved = sum(r.tokens_saved for r in results)
        
        logger.info(
            f"Comprimidos {len(results)} chunks: "
            f"{total_original} → {total_compressed} chars "
            f"({total_saved} tokens economizados)"
        )
        
        return results
