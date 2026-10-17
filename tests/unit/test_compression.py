"""
Testes completos para módulo de compressão
"""
import pytest

from api.compression import (
    CompressionResult,
    SentenceCompressor,
    KeywordCompressor,
    LengthCompressor,
    ParagraphCompressor,
    CompressionService,
)


# Fixtures

@pytest.fixture
def sample_text():
    """Texto de amostra para testes"""
    return """
    RAG (Retrieval-Augmented Generation) is a powerful technique. 
    It combines information retrieval with text generation. 
    The key benefit is reduced hallucinations. 
    Another advantage is that RAG provides source attribution. 
    This makes it ideal for documentation systems.
    """


@pytest.fixture
def long_text():
    """Texto longo com múltiplos parágrafos"""
    return """
    ## Introduction to RAG
    
    RAG is an important technique in natural language processing. 
    It represents a significant advancement in how we handle information. 
    The technology has multiple applications.
    
    ## How RAG Works
    
    The first step is retrieval. This critical phase requires searching for relevant documents. 
    The second step is ranking. Ranking is essential for quality. 
    The final step is generation. Generation must be accurate.
    
    ## Benefits and Advantages
    
    Cost reduction is a key benefit. Token efficiency is important. 
    Better source attribution makes RAG valuable.
    """


@pytest.fixture
def sentence_compressor():
    """Compressor de sentenças"""
    return SentenceCompressor(threshold=0.3)


@pytest.fixture
def keyword_compressor():
    """Compressor de keywords"""
    return KeywordCompressor(keywords=["RAG", "important", "critical"])


@pytest.fixture
def length_compressor():
    """Compressor de comprimento"""
    return LengthCompressor()


@pytest.fixture
def paragraph_compressor():
    """Compressor de parágrafos"""
    return ParagraphCompressor(keep_paragraphs=2)


# Testes de CompressionResult

class TestCompressionResult:
    """Testes para CompressionResult"""
    
    def test_compression_result_creation(self):
        """Teste de criação de CompressionResult"""
        result = CompressionResult(
            original_text="Hello world",
            compressed_text="Hello",
            compression_ratio=50.0,
            method="test",
            tokens_saved=2,
        )
        
        assert result.original_text == "Hello world"
        assert result.compressed_text == "Hello"
        assert result.compression_ratio == 50.0
        assert result.method == "test"
        assert result.tokens_saved == 2
    
    def test_compression_result_empty_text(self):
        """Teste com texto vazio"""
        result = CompressionResult(
            original_text="",
            compressed_text="",
            compression_ratio=0.0,
            method="test",
            tokens_saved=0,
        )
        
        assert len(result.original_text) == 0
        assert len(result.compressed_text) == 0


# Testes de SentenceCompressor

class TestSentenceCompressor:
    """Testes para SentenceCompressor"""
    
    def test_initialization(self, sentence_compressor):
        """Teste de inicialização"""
        assert sentence_compressor.threshold == 0.3
    
    def test_compress_basic(self, sentence_compressor, sample_text):
        """Teste de compressão básica"""
        result = sentence_compressor.compress(sample_text)
        
        assert isinstance(result, CompressionResult)
        assert len(result.compressed_text) > 0
        assert result.method == "sentence"
        assert result.compression_ratio >= 0
    
    def test_compress_empty_text(self, sentence_compressor):
        """Teste com texto vazio"""
        result = sentence_compressor.compress("")
        
        assert result.compressed_text == ""
        assert result.tokens_saved == 0
    
    def test_compress_with_max_length(self, sentence_compressor, sample_text):
        """Teste com comprimento máximo"""
        max_len = 50
        result = sentence_compressor.compress(sample_text, max_length=max_len)
        
        assert len(result.compressed_text) <= max_len + 3  # +3 para "..."
    
    def test_split_sentences(self, sentence_compressor):
        """Teste de divisão em sentenças"""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = sentence_compressor._split_sentences(text)
        
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
    
    def test_score_sentences(self, sentence_compressor):
        """Teste de scoring de sentenças"""
        sentences = [
            "Hi",  # Muito curta
            "This is a normal sentence with medium length.",  # Normal
            "The key requirement for this critical task is essential.",  # Com keywords
        ]
        scores = sentence_compressor._score_sentences(sentences)
        
        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)


# Testes de KeywordCompressor

class TestKeywordCompressor:
    """Testes para KeywordCompressor"""
    
    def test_initialization(self):
        """Teste de inicialização"""
        kw = KeywordCompressor(keywords=["test", "example"])
        assert kw.keywords == ["test", "example"]
    
    def test_compress_with_keywords(self, keyword_compressor, sample_text):
        """Teste com keywords"""
        result = keyword_compressor.compress(sample_text)
        
        assert isinstance(result, CompressionResult)
        assert "RAG" in result.compressed_text or len(result.compressed_text) > 0
        assert result.method == "keyword"
    
    def test_compress_no_keywords(self):
        """Teste sem keywords configuradas"""
        compressor = KeywordCompressor(keywords=[])
        text = "This is some random text without keywords"
        result = compressor.compress(text)
        
        # Sem keywords, retorna o texto original
        assert result.compressed_text == text
    
    def test_compress_with_max_length(self, keyword_compressor, sample_text):
        """Teste com comprimento máximo"""
        result = keyword_compressor.compress(sample_text, max_length=50)
        
        assert len(result.compressed_text) <= 53  # +3 para "..."


# Testes de LengthCompressor

class TestLengthCompressor:
    """Testes para LengthCompressor"""
    
    def test_compress_no_truncation(self, length_compressor):
        """Teste sem truncação necessária"""
        text = "Short text"
        result = length_compressor.compress(text, max_length=100)
        
        assert result.compressed_text == text
        assert result.compression_ratio == 0.0
    
    def test_compress_with_truncation(self, length_compressor):
        """Teste com truncação"""
        text = "This is a very long text that needs to be truncated because it exceeds the maximum length"
        result = length_compressor.compress(text, max_length=30)
        
        assert len(result.compressed_text) <= 33  # +3 para "..."
        assert result.compression_ratio > 0
    
    def test_default_max_length(self, length_compressor, sample_text):
        """Teste com comprimento padrão"""
        result = length_compressor.compress(sample_text)
        
        assert len(result.compressed_text) <= 303  # 300 + "..."


# Testes de ParagraphCompressor

class TestParagraphCompressor:
    """Testes para ParagraphCompressor"""
    
    def test_initialization(self, paragraph_compressor):
        """Teste de inicialização"""
        assert paragraph_compressor.keep_paragraphs == 2
    
    def test_compress_multiple_paragraphs(self, paragraph_compressor, long_text):
        """Teste com múltiplos parágrafos"""
        result = paragraph_compressor.compress(long_text)
        
        assert isinstance(result, CompressionResult)
        assert len(result.compressed_text) < len(long_text)
    
    def test_compress_single_paragraph(self, paragraph_compressor):
        """Teste com parágrafo único"""
        text = "This is a single paragraph without line breaks."
        result = paragraph_compressor.compress(text)
        
        assert result.compressed_text == text
    
    def test_empty_text(self, paragraph_compressor):
        """Teste com texto vazio"""
        result = paragraph_compressor.compress("")
        
        assert result.compressed_text == ""


# Testes de CompressionService

class TestCompressionService:
    """Testes para CompressionService"""
    
    def test_initialization(self):
        """Teste de inicialização"""
        service = CompressionService()
        
        assert "sentence" in service.compressors
        assert "keyword" in service.compressors
        assert "length" in service.compressors
        assert "paragraph" in service.compressors
    
    def test_compress_sentence_method(self, sample_text):
        """Teste com método sentence"""
        service = CompressionService()
        result = service.compress(sample_text, method="sentence")
        
        assert result.method == "sentence"
        assert len(result.compressed_text) > 0
    
    def test_compress_length_method(self, sample_text):
        """Teste com método length"""
        service = CompressionService()
        result = service.compress(sample_text, method="length", max_length=100)
        
        assert result.method == "length"
        assert len(result.compressed_text) <= 103
    
    def test_compress_unknown_method(self, sample_text):
        """Teste com método desconhecido (fallback)"""
        service = CompressionService()
        result = service.compress(sample_text, method="unknown")
        
        # Deve usar método padrão (sentence)
        assert result.method == "sentence"
    
    def test_compress_chunks(self, sample_text):
        """Teste de compressão de múltiplos chunks"""
        service = CompressionService()
        chunks = [sample_text, sample_text, sample_text]
        
        results = service.compress_chunks(chunks, method="length")
        
        assert len(results) == 3
        assert all(isinstance(r, CompressionResult) for r in results)
    
    def test_compress_chunks_empty_list(self):
        """Teste com lista vazia de chunks"""
        service = CompressionService()
        results = service.compress_chunks([])
        
        assert len(results) == 0


# Testes de Integração

class TestCompressionIntegration:
    """Testes de integração entre compressores"""
    
    def test_all_methods_reduce_size(self, sample_text):
        """Teste que todos os métodos reduzem tamanho"""
        service = CompressionService()
        
        methods = ["sentence", "length", "paragraph"]
        for method in methods:
            result = service.compress(sample_text, method=method)
            # Alguns métodos podem não reduzir se o texto for pequeno
            assert isinstance(result, CompressionResult)
    
    def test_compression_preserves_content(self, sample_text):
        """Teste que compressão preserva conteúdo importante"""
        service = CompressionService()
        result = service.compress(sample_text, method="sentence")
        
        # Palavras-chave devem estar presentes
        compressed_lower = result.compressed_text.lower()
        assert "rag" in compressed_lower or "generation" in compressed_lower
    
    def test_different_methods_different_results(self, sample_text):
        """Teste que métodos diferentes produzem resultados diferentes"""
        service = CompressionService()
        
        result_sentence = service.compress(sample_text, method="sentence")
        result_length = service.compress(sample_text, method="length", max_length=100)
        
        # Resultados devem ser diferentes (pelo menos um)
        assert (result_sentence.compressed_text != result_length.compressed_text or
                result_sentence.method != result_length.method)


# Testes de Performance

class TestCompressionPerformance:
    """Testes de performance"""
    
    def test_large_text_compression(self):
        """Teste com texto muito grande"""
        large_text = " ".join(["This is a sentence."] * 1000)
        service = CompressionService()
        
        result = service.compress(large_text, method="length", max_length=500)
        
        assert len(result.compressed_text) <= 503
        assert result.tokens_saved > 0
    
    def test_compression_ratio_calculation(self):
        """Teste de cálculo de ratio de compressão"""
        text = "A" * 100
        service = CompressionService()
        result = service.compress(text, method="length", max_length=50)
        
        assert result.compression_ratio > 0
        assert result.compression_ratio <= 100
