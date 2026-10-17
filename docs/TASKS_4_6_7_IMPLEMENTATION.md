# TASKS 4, 6, 7: Pipeline RAG Completo

## Resumo Executivo

Implementação completa do pipeline RAG (Retrieval-Augmented Generation) para Docky com três componentes principais:

### ✅ TASK #4: Busca Vetorial e Re-ranking
- **Arquivo**: `api/search.py`
- **Classe**: `SearchService`
- **Funcionalidade**:
  - Integração com Qdrant (Vector DB)
  - Busca vetorial por similaridade (cosine)
  - Re-ranking com `bge-reranker-base` (CrossEncoder)
  - Chunking automático com sobreposição
  - Endpoint: `POST /search`

### ✅ TASK #6: Modelfiles Ollama
- **Arquivos**: `llm/Modelfile.phi` e `llm/Modelfile.qwen`
- **Funcionalidade**:
  - Prefix caching ativado
  - Prompts templates compactos
  - Phi-3.5-mini: 4KB contexto, ~200-400ms latência
  - Qwen2.5-3B: 8KB contexto, ~400-800ms latência

### ✅ TASK #7: Pipeline RAG Completo
- **Arquivo**: `api/rag.py`
- **Classe**: `RAGService`
- **Funcionalidade**:
  - Pipeline: Search → Rerank → Compress → Prompt → LLM
  - Compressão extrativa de chunks
  - Gerenciamento de tokens
  - Endpoint: `POST /ask`

---

## Arquitetura Detalhada

### Fluxo de Uma Query

```
User Query: "O que é RAG?"
    ↓
[1. SearchService.search_with_reranking()]
    ├─ Embedding da query (sentence-transformers)
    ├─ Busca no Qdrant (top-15 candidatos)
    ├─ Re-ranking com bge-reranker-base (top-5)
    └─ Returns: list[SearchResult]
    ↓
[2. RAGService.ask()]
    ├─ Compressão extrativa do contexto
    ├─ Construção de prompt compacto
    ├─ Geração com OllamaClient
    └─ Returns: RAGResponse
    ↓
User: <answer> + sources + confidence
```

### Componentes

#### 1. SearchService (api/search.py)

```python
# Inicialização
search_service = SearchService(
    qdrant_url="http://localhost:6333",
    collection_name="docky_documents",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
)

# Garantir collection
await search_service.ensure_collection()

# Busca com re-ranking
results = await search_service.search_with_reranking(
    query="What is RAG?",
    top_k_initial=15,    # Candidatos da busca vetorial
    top_k_reranked=5,    # Resultados finais
    similarity_threshold=0.5,
)
```

**Métodos principais**:

| Método | Args | Retorna | Descrição |
|--------|------|---------|-----------|
| `ensure_collection()` | - | bool | Cria collection se não existir |
| `index_document()` | doc_id, content, metadata | int | Indexa documento em chunks |
| `search()` | query, top_k, threshold | list[SearchResult] | Busca por similaridade |
| `search_with_reranking()` | query, top_k_initial, top_k_reranked | list[SearchResult] | Busca + re-ranking |

**SearchResult**:

```python
@dataclass
class SearchResult:
    content: str          # Texto do chunk
    metadata: dict        # {file_name, file_path, chunk_index, ...}
    score: float          # Score do re-ranker (0-1)
    rank: int             # Posição (1, 2, 3, ...)
```

#### 2. RAGService (api/rag.py)

```python
# Inicialização
rag_service = RAGService(
    search_service=search_service,
    llm_client=ollama_client,
    max_chunk_length=300,        # Tamanho máximo de chunk na resposta
    max_context_tokens=2000,     # Limite de tokens do contexto
)

# Processar pergunta
response = await rag_service.ask(
    query="What is RAG?",
    top_k_initial=15,
    top_k_reranked=5,
    similarity_threshold=0.5,
    temperature=0.3,  # Optional: override LLM temperature
)

# response.answer: str
# response.source_documents: list[dict]
# response.confidence: float (0-1)
# response.retrieval_time_ms: float
# response.generation_time_ms: float
```

**Métodos principais**:

| Método | Descrição |
|--------|-----------|
| `ask()` | Pipeline RAG completo |
| `_compress_context()` | Extrai trechos relevantes |
| `_build_prompt()` | Constrói prompt estruturado |

#### 3. OllamaClient (llm/client.py) - Existente

```python
# Já implementado, usado por RAGService
ollama_client = OllamaClient(
    base_url="http://localhost:11434",
    model="docky-phi",  # ou "docky-qwen"
    temperature=0.3,
)

response = await ollama_client.generate(
    prompt=prompt_text,
    temperature=0.3,
    max_tokens=512,
)
```

---

## Endpoints da API

### POST /search
Busca vetorial com re-ranking.

**Request**:
```json
{
  "query": "O que é RAG?",
  "top_k_initial": 15,
  "top_k_reranked": 5,
  "similarity_threshold": 0.5
}
```

**Response**:
```json
{
  "query": "O que é RAG?",
  "results_count": 5,
  "results": [
    {
      "rank": 1,
      "file_name": "rag-guide.md",
      "content": "RAG é Retrieval-Augmented Generation...",
      "score": 0.92,
      "chunk_index": 0
    },
    ...
  ],
  "retrieval_time_ms": 145.3
}
```

### POST /ask
Pipeline RAG completo: busca → rerank → compress → prompt → LLM.

**Request**:
```json
{
  "query": "O que é RAG?",
  "top_k_initial": 15,
  "top_k_reranked": 5,
  "similarity_threshold": 0.5,
  "temperature": 0.3
}
```

**Response**:
```json
{
  "answer": "RAG (Retrieval-Augmented Generation) é uma técnica que combina busca de informações com geração de texto...",
  "sources": [
    {
      "rank": 1,
      "file_name": "rag-guide.md",
      "relevance_score": 0.92,
      "preview": "RAG é Retrieval-Augmented Generation..."
    },
    ...
  ],
  "confidence": 0.92,
  "retrieval_time_ms": 145.3,
  "generation_time_ms": 287.5
}
```

---

## Teste com cURL

### Test SearchService

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k_initial": 15,
    "top_k_reranked": 5
  }'
```

### Test RAGService

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k_reranked": 5,
    "temperature": 0.3
  }'
```

---

## Configurações (pyproject.toml e .env)

### pyproject.toml

Dependências já incluídas:
- `sentence-transformers>=2.2.0` - Embeddings e re-ranking
- `qdrant-client>=2.7.0` - Vector DB client
- `fastapi>=0.104.0` - API framework
- `httpx>=0.24.0` - HTTP client async

### .env

```env
# Search
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=docky_documents
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# RAG
RETRIEVAL_TOP_K=15
RETRIEVAL_SIMILARITY_THRESHOLD=0.5
ENABLE_RERANKING=true

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=docky-phi  # ou docky-qwen
OLLAMA_TEMPERATURE=0.3
```

---

## Modelfiles Ollama

### Criar Modelos Custom

```bash
# Phi-3.5-mini com prefix caching
ollama create docky-phi -f ./llm/Modelfile.phi

# Qwen2.5-3B com prefix caching
ollama create docky-qwen -f ./llm/Modelfile.qwen
```

### Usar na API

```bash
# Atualizar .env
OLLAMA_MODEL=docky-phi

# Reiniciar API
uvicorn api.main:app --reload
```

### Características dos Modelfiles

#### Phi-3.5-mini (Modelfile.phi)
- **Tamanho**: ~2.2GB
- **Contexto**: 4K tokens
- **Latência**: 200-400ms
- **Memory**: 3-4GB RAM
- **Ideal para**: Respostas rápidas, respostas curtas

#### Qwen2.5-3B (Modelfile.qwen)
- **Tamanho**: ~2.0GB
- **Contexto**: 8K tokens
- **Latência**: 400-800ms
- **Memory**: 5-6GB RAM
- **Ideal para**: Melhor qualidade, contexto maior

---

## Performance e Otimizações

### Latência Esperada

| Etapa | Tempo | Notas |
|-------|-------|-------|
| Embedding query | ~50ms | Rápido, local |
| Busca Qdrant | ~50-100ms | Depende do tamanho da collection |
| Re-ranking (5 docs) | ~30-50ms | Local, rápido |
| Geração LLM | 200-800ms | Depende do modelo (Phi vs Qwen) |
| **Total** | **350-1050ms** | Para resposta completa |

### Token Economy

- **Query**: ~10-20 tokens
- **Contexto**: ~500-2000 tokens
- **Prompt template**: ~50 tokens
- **Response**: ~100-512 tokens
- **Total**: ~700-2500 tokens por query

### Otimizações Implementadas

1. **Prefix Caching** (Ollama Modelfiles)
   - KV cache para reusar computação
   - Reduce latência em queries sucessivas

2. **Compressão Extrativa**
   - Remove partes irrelevantes do contexto
   - Reduz tokens necessários

3. **Re-ranking Local**
   - Descarta documentos ruins antes de passar ao LLM
   - CrossEncoder rápido (BAAI/bge-reranker-base)

4. **Chunking com Sobreposição**
   - Garante que informações não sejam perdidas
   - Overlap de 50 caracteres por padrão

---

## Testes

### Unit Tests

```bash
# Rodar todos os testes
pytest

# Apenas SearchService
pytest tests/unit/test_search.py -v

# Apenas RAGService
pytest tests/unit/test_rag.py -v

# Com cobertura
pytest --cov=api --cov=llm
```

### Testes Implementados

1. **test_search.py**
   - Inicialização do SearchService
   - Chunking de texto com sobreposição
   - SearchResult model

2. **test_rag.py**
   - Inicialização do RAGService
   - Compressão de contexto
   - Construção de prompt
   - RAGResponse model

---

## Stack Completo

| Componente | Versão | Propósito |
|------------|--------|-----------|
| **Python** | 3.10+ | Runtime |
| **FastAPI** | 0.104+ | API framework |
| **Uvicorn** | 0.24+ | ASGI server |
| **Qdrant** | 2.7+ | Vector database |
| **Sentence-Transformers** | 2.2+ | Embeddings & re-ranking |
| **Ollama** | Latest | Local LLM engine |
| **Pydantic** | 2.0+ | Data validation |
| **HTTPX** | 0.24+ | Async HTTP |

---

## Próximas Etapas (Não Implementadas)

- [ ] Persistência de índices
- [ ] Ingestão em batch
- [ ] Fine-tuning de embeddings
- [ ] Caching de embeddings
- [ ] Monitoring e observabilidade
- [ ] Rate limiting
- [ ] Autenticação (JWT/API key)

---

## Referências

### Documentação
- [Qdrant](https://qdrant.tech/documentation/)
- [Sentence-Transformers](https://www.sbert.net/)
- [BAAI/bge-reranker](https://huggingface.co/BAAI/bge-reranker-base)
- [Ollama](https://ollama.ai/)

### Modelos
- [Phi-3.5-mini](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)
- [Qwen2.5-3B](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
