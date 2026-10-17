# 🧪 Testing Guide: TASKS 4, 6, 7

## Setup Inicial

### 1. Instalar Dependências
```bash
cd /Users/rafaelnc/apps/docky
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 2. Iniciar Serviços (Docker)
```bash
docker-compose up -d qdrant ollama

# Verificar
docker-compose ps
```

### 3. Baixar Modelos Ollama
```bash
# Terminal 1: Verifique o status do Ollama
docker-compose logs -f ollama

# Terminal 2: Baixe um modelo
ollama pull phi3.5
# ou
ollama pull qwen2.5

# Crie modelo custom (recomendado)
ollama create docky-phi -f ./llm/Modelfile.phi
```

---

## Testes Unitários

### Rodar Todos os Testes
```bash
pytest -v

# Com cobertura
pytest --cov=api --cov=llm --cov-report=term-missing
```

### Testes de SearchService
```bash
pytest tests/unit/test_search.py -v

# Testes específicos
pytest tests/unit/test_search.py::test_chunk_text_basic -v
pytest tests/unit/test_search.py::test_search_result -v
```

### Testes de RAGService
```bash
pytest tests/unit/test_rag.py -v

# Testes específicos
pytest tests/unit/test_rag.py::test_rag_service_initialization -v
pytest tests/unit/test_rag.py::test_compress_context -v
pytest tests/unit/test_rag.py::test_build_prompt -v
```

---

## Testes de Integração (Manual)

### 1. Inicie a API
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Health Check
```bash
curl http://localhost:8000/health

# Esperado:
# {"status":"ok","timestamp":"...","services":{"qdrant":true,"ollama":true}}
```

### 3. Teste SearchService - POST /search

#### Request
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k_initial": 15,
    "top_k_reranked": 5,
    "similarity_threshold": 0.5
  }' | jq .
```

#### Esperado
```json
{
  "query": "What is RAG?",
  "results_count": 0,
  "results": [],
  "retrieval_time_ms": null
}
```

Note: Retorna vazio porque ainda não há documentos indexados.

### 4. Teste RAGService - POST /ask

#### Request
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k_initial": 15,
    "top_k_reranked": 5,
    "similarity_threshold": 0.5,
    "temperature": 0.3
  }' | jq .
```

#### Esperado
```json
{
  "answer": "Desculpe, não consegui encontrar informações relevantes sobre isso na documentação.",
  "sources": [],
  "confidence": 0.0,
  "retrieval_time_ms": 25.3,
  "generation_time_ms": null
}
```

---

## Teste End-to-End com Exemplo

### 1. Execute o Exemplo
```bash
python examples/rag_pipeline_example.py
```

### 2. Output Esperado
```
🚀 Inicializando Docky RAG Pipeline
✅ Indexados 8 chunks
============================================================
Query: O que é RAG?
============================================================
✅ Resposta:
RAG (Retrieval-Augmented Generation) é uma abordagem que...

Confiança: 95%
Tempo de recuperação: 145.3ms
Tempo de geração: 287.5ms

Fontes (5):
  [1] rag_guide.md (score: 0.950)
  ...
```

---

## Teste com Documentos Reais

### 1. Crie um Documento de Teste
```bash
mkdir -p data/raw
cat > data/raw/test_doc.md << 'EOF'
# Introduction to RAG

RAG (Retrieval-Augmented Generation) combines information retrieval with text generation.

## How RAG Works

1. **Retrieval**: Search for relevant documents
2. **Ranking**: Score documents by relevance
3. **Generation**: Use documents to generate responses

## Benefits

- Reduced hallucinations
- Up-to-date information
- Source attribution
- Token efficiency
EOF
```

### 2. Indexe o Documento (em exemplo_with_file.py)
```python
import asyncio
from api.search import SearchService

async def main():
    service = SearchService()
    await service.ensure_collection()
    
    with open('data/raw/test_doc.md', 'r') as f:
        content = f.read()
    
    chunks = await service.index_document(
        doc_id="test_doc",
        content=content,
        metadata={
            "file_name": "test_doc.md",
            "file_path": "data/raw/test_doc.md"
        }
    )
    print(f"Indexed {chunks} chunks")
    await service.close()

asyncio.run(main())
```

### 3. Teste Novamente
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}' | jq .
```

---

## Teste de Performance

### Latência
```bash
# Benchmark /search
time curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}'

# Benchmark /ask
time curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}'
```

### Throughput
```bash
# 10 requests em paralelo
for i in {1..10}; do
  curl -X POST http://localhost:8000/ask \
    -H "Content-Type: application/json" \
    -d '{"query": "What is RAG?"}' &
done
wait
```

---

## Teste de Logs

### Verificar Logs da API
```bash
# Terminal 1: Watch logs
tail -f logs/api.log 2>/dev/null || echo "Logs não configurados ainda"

# Terminal 2: Fazer request
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Debug Mode
```bash
DEBUG=true uvicorn api.main:app --reload
```

---

## Validação Checklist

### SearchService ✅
- [ ] Inicializa sem erros
- [ ] Cria collection no Qdrant
- [ ] Indexa documentos corretamente
- [ ] Busca retorna resultados
- [ ] Re-ranking funciona
- [ ] Chunking com overlap funciona

### RAGService ✅
- [ ] Inicializa com SearchService e OllamaClient
- [ ] Pipeline complete executa
- [ ] Contexto é comprimido
- [ ] Prompt é construído corretamente
- [ ] LLM gera resposta
- [ ] Métricas de performance são calculadas

### API Endpoints ✅
- [ ] GET / funciona
- [ ] POST /search funciona
- [ ] POST /ask funciona
- [ ] POST /query funciona (deprecated)
- [ ] GET /health funciona

### Documentação ✅
- [ ] QUICKSTART.md completo
- [ ] TASKS_4_6_7_IMPLEMENTATION.md detalhado
- [ ] llm/MODELFILES.md documentado
- [ ] examples/rag_pipeline_example.py executável

---

## Troubleshooting

### Erro: "Qdrant not responding"
```bash
# Verificar status
curl http://localhost:6333/health

# Reiniciar
docker-compose restart qdrant

# Esperar initialization
sleep 5
```

### Erro: "Ollama models not found"
```bash
# List models
ollama list

# Pull model
ollama pull phi3.5

# Create custom
ollama create docky-phi -f ./llm/Modelfile.phi
```

### Erro: "CrossEncoder not loading"
```bash
# Testa import
python -c "from sentence_transformers import CrossEncoder; print('OK')"

# Reinstala
pip install --upgrade sentence-transformers
```

### Erro: Memory issues
- Use Phi-3.5-mini em vez de Qwen
- Reduza EMBEDDING_DIMENSION
- Reduza RETRIEVAL_TOP_K

---

## Próximos Testes

- [ ] Teste de integração com document loaders
- [ ] Teste com múltiplas queries em paralelo
- [ ] Teste de persistência de índices
- [ ] Teste de refresh/re-indexing
- [ ] Load testing com k6 ou locusts

---

## Referência Rápida

| Comando | Função |
|---------|--------|
| `pytest` | Rodar todos os testes |
| `pytest -v` | Testes com verbose |
| `pytest --cov` | Com cobertura |
| `uvicorn api.main:app --reload` | Inicia API |
| `curl -X POST ...` | Testa endpoint |
| `ollama pull phi3.5` | Baixa modelo |
| `docker-compose ps` | Verificar serviços |

---

**Última atualização**: 2026-10-17
