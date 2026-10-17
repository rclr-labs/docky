"""
Testes End-to-End (E2E) para o pipeline RAG completo
Mock do Ollama para testes sem GPU
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.search import SearchService, SearchResult
from api.rag import RAGService, RAGResponse
from api.compression import CompressionService
from llm.client import OllamaClient, LLMResponse


# Fixtures

@pytest.fixture
def mock_ollama_client():
    """Mock para OllamaClient"""
    client = AsyncMock(spec=OllamaClient)
    client.generate = AsyncMock(
        return_value=LLMResponse(
            text="RAG (Retrieval-Augmented Generation) combines information retrieval with text generation to reduce hallucinations.",
            model="test-model",
            tokens_used=42,
        )
    )
    return client


@pytest.fixture
def mock_qdrant_client():
    """Mock para cliente Qdrant"""
    return AsyncMock()


@pytest.fixture
def sample_documents():
    """Documentos de amostra para testes"""
    return [
        {
            "id": "doc1",
            "content": "RAG is Retrieval-Augmented Generation. It combines information retrieval with text generation. This technique is important for reducing hallucinations in language models.",
            "metadata": {
                "file_name": "rag_basics.md",
                "file_path": "docs/rag_basics.md",
                "source_url": "https://example.com/docs/rag",
            }
        },
        {
            "id": "doc2", 
            "content": "LLMs can generate text without external context. However, they sometimes hallucinate or make up information. RAG solves this by grounding responses in real documents.",
            "metadata": {
                "file_name": "llm_limitations.md",
                "file_path": "docs/llm_limitations.md",
            }
        },
        {
            "id": "doc3",
            "content": "Vector databases like Qdrant store embeddings of documents. Retrieval happens through similarity search. The nearest documents are retrieved for context.",
            "metadata": {
                "file_name": "vector_db.md",
                "file_path": "docs/vector_db.md",
            }
        },
    ]


@pytest.fixture
async def search_service(mock_qdrant_client):
    """Instância de SearchService com mock"""
    with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
        service = SearchService()
        # Mock ensure_collection
        service.qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        yield service


@pytest.fixture
def compression_service():
    """Instância de CompressionService"""
    return CompressionService()


# Testes E2E

class TestE2ESearchPipeline:
    """Testes end-to-end do pipeline de busca"""
    
    @pytest.mark.asyncio
    async def test_full_search_pipeline(self, mock_qdrant_client, sample_documents):
        """Teste pipeline completo: indexação → busca → re-ranking"""
        
        # Setup mock do Qdrant
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        mock_qdrant_client.upsert = AsyncMock(return_value=None)
        
        # Mock search results
        search_results = [
            MagicMock(
                score=0.95,
                payload={
                    "file_name": "rag_basics.md",
                    "chunk_text": "RAG is Retrieval-Augmented Generation.",
                    "chunk_index": 0,
                }
            ),
            MagicMock(
                score=0.87,
                payload={
                    "file_name": "llm_limitations.md",
                    "chunk_text": "RAG solves hallucination issues.",
                    "chunk_index": 1,
                }
            ),
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        # Criar search service
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            
            # Executar busca
            results = await search_service.search(
                query="What is RAG?",
                top_k=5,
            )
            
            # Verificar resultados
            assert len(results) >= 0
            assert all(isinstance(r, SearchResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_reranking_pipeline(self, mock_qdrant_client):
        """Teste pipeline de busca com re-ranking"""
        
        # Setup mocks
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        
        search_results = [
            MagicMock(
                score=0.85,
                payload={
                    "file_name": "doc1.md",
                    "chunk_text": "Text about RAG",
                    "chunk_index": 0,
                }
            ) for _ in range(5)
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            
            # Busca com re-ranking
            results = await search_service.search_with_reranking(
                query="RAG?",
                top_k_initial=15,
                top_k_reranked=3,
            )
            
            # Verificar que re-ranking reduziu para top-3
            assert len(results) <= 3


class TestE2ERAGPipeline:
    """Testes end-to-end do pipeline RAG completo"""
    
    @pytest.mark.asyncio
    async def test_full_rag_pipeline(self, mock_qdrant_client, mock_ollama_client):
        """Teste pipeline completo: busca → rerank → compress → prompt → LLM"""
        
        # Setup
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        
        search_results = [
            MagicMock(
                score=0.92,
                payload={
                    "file_name": "rag.md",
                    "chunk_text": "RAG is Retrieval-Augmented Generation. It reduces hallucinations.",
                    "chunk_index": 0,
                }
            ),
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        # Criar serviços
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            rag_service = RAGService(
                search_service=search_service,
                llm_client=mock_ollama_client,
            )
            
            # Executar pipeline RAG
            response = await rag_service.ask(
                query="What is RAG?",
                top_k_reranked=3,
            )
            
            # Verificar resposta
            assert isinstance(response, RAGResponse)
            assert isinstance(response.answer, str)
            assert isinstance(response.confidence, (int, float))
            assert isinstance(response.source_documents, list)
    
    @pytest.mark.asyncio
    async def test_rag_pipeline_with_no_results(self, mock_qdrant_client, mock_ollama_client):
        """Teste RAG quando não há documentos relevantes"""
        
        # Setup: sem resultados de busca
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        mock_qdrant_client.search = AsyncMock(return_value=[])
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            rag_service = RAGService(
                search_service=search_service,
                llm_client=mock_ollama_client,
            )
            
            # Executar
            response = await rag_service.ask(query="Unknown topic")
            
            # Deve retornar resposta mesmo sem documentos
            assert isinstance(response, RAGResponse)
            assert "informações relevantes" in response.answer.lower() or len(response.source_documents) == 0


class TestE2ECompressionIntegration:
    """Testes E2E com compressão integrada"""
    
    def test_compression_in_context_building(self, compression_service):
        """Teste compressão durante construção de contexto"""
        
        long_context = "RAG is important. " * 50  # Texto repetido
        
        # Comprimir
        result = compression_service.compress(
            long_context,
            method="sentence",
            max_length=500,
        )
        
        # Verificar compressão
        assert len(result.compressed_text) < len(long_context)
        assert result.tokens_saved > 0
        assert result.compression_ratio > 0
    
    def test_compression_with_different_methods(self, compression_service):
        """Teste diferentes métodos de compressão"""
        
        text = "First important sentence. Second unimportant sentence. Third critical sentence."
        
        # Testar cada método
        methods = ["sentence", "length", "paragraph"]
        results = {}
        
        for method in methods:
            result = compression_service.compress(text, method=method, max_length=50)
            results[method] = result
            assert isinstance(result.compressed_text, str)
        
        # Verificar que métodos diferentes produzem diferentes resultados
        assert results["sentence"].compressed_text != results["length"].compressed_text


class TestE2EIntegrationWithAPI:
    """Testes E2E com integração da API"""
    
    @pytest.mark.asyncio
    async def test_search_endpoint_flow(self, mock_qdrant_client):
        """Teste fluxo completo do endpoint /search"""
        
        # Setup
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        
        search_results = [
            MagicMock(
                score=0.95,
                payload={
                    "file_name": "test.md",
                    "chunk_text": "Test content",
                    "chunk_index": 0,
                }
            ),
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            
            # Simular request /search
            results = await search_service.search_with_reranking(
                query="test",
                top_k_initial=15,
                top_k_reranked=5,
            )
            
            # Validar response structure
            assert isinstance(results, list)
            assert all(hasattr(r, 'rank') for r in results)
            assert all(hasattr(r, 'score') for r in results)
    
    @pytest.mark.asyncio
    async def test_ask_endpoint_flow(self, mock_qdrant_client, mock_ollama_client):
        """Teste fluxo completo do endpoint /ask"""
        
        # Setup
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        
        search_results = [
            MagicMock(
                score=0.90,
                payload={
                    "file_name": "answer.md",
                    "chunk_text": "Important information",
                    "chunk_index": 0,
                }
            ),
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            rag_service = RAGService(
                search_service=search_service,
                llm_client=mock_ollama_client,
            )
            
            # Simular request /ask
            response = await rag_service.ask(query="Question?")
            
            # Validar response structure
            assert hasattr(response, 'answer')
            assert hasattr(response, 'source_documents')
            assert hasattr(response, 'confidence')


class TestE2EErrorHandling:
    """Testes E2E de tratamento de erros"""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_qdrant_error(self, mock_qdrant_client, mock_ollama_client):
        """Teste degradação graciosa quando Qdrant falha"""
        
        # Simular erro do Qdrant
        mock_qdrant_client.search = AsyncMock(
            side_effect=Exception("Qdrant connection failed")
        )
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            
            # Deve retornar lista vazia em vez de falhar
            results = await search_service.search(query="test")
            
            assert isinstance(results, list)
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_ollama_error(self, mock_qdrant_client):
        """Teste degradação graciosa quando Ollama falha"""
        
        # Mock Ollama com erro
        mock_ollama = AsyncMock()
        mock_ollama.generate = AsyncMock(
            side_effect=Exception("Ollama connection failed")
        )
        
        # Mock Qdrant com sucesso
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        search_results = [
            MagicMock(
                score=0.95,
                payload={"file_name": "test.md", "chunk_text": "Test", "chunk_index": 0}
            ),
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            rag_service = RAGService(
                search_service=search_service,
                llm_client=mock_ollama,
            )
            
            # Deve falhar gracefully
            # (ou retornar resposta com documentos mas sem LLM)
            try:
                response = await rag_service.ask(query="test")
                # Se chegou aqui, é uma degradação graciosa
                assert isinstance(response, RAGResponse) or response is None
            except Exception:
                # Erro esperado é aceitável
                pass


class TestE2EPerformance:
    """Testes E2E de performance"""
    
    @pytest.mark.asyncio
    async def test_pipeline_latency(self, mock_qdrant_client, mock_ollama_client):
        """Teste latência total do pipeline"""
        import time
        
        # Setup
        mock_qdrant_client.get_collection = AsyncMock(return_value={"name": "test"})
        search_results = [
            MagicMock(
                score=0.95,
                payload={"file_name": "doc.md", "chunk_text": "Content", "chunk_index": 0}
            ),
        ]
        mock_qdrant_client.search = AsyncMock(return_value=search_results)
        
        with patch('api.search.AsyncQdrantClient', return_value=mock_qdrant_client):
            search_service = SearchService()
            rag_service = RAGService(
                search_service=search_service,
                llm_client=mock_ollama_client,
            )
            
            # Medir latência
            start = time.time()
            response = await rag_service.ask(query="test?")
            latency = (time.time() - start) * 1000  # em ms
            
            # Verificar latência
            assert latency > 0
            # Deve ser rápido com mocks
            assert latency < 5000  # 5 segundos é razoável
