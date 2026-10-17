# Quick Start: Docky RAG Pipeline

## 📋 Pré-requisitos

- Python 3.10+
- Docker & Docker Compose
- ~6GB de memória RAM disponível

## 🚀 Setup Rápido

### 1. Clone e Configure

```bash
cd docky
cp .env.example .env
```

### 2. Inicie os Serviços com Docker Compose

```bash
docker-compose up -d

# Verificar status
docker-compose ps
```

### 3. Instale Dependências Python

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -e ".[dev]"
```

### 4. Baixe um Modelo Ollama

```bash
# Opção A: Phi-3.5-mini (rápido, 2.2GB)
ollama pull phi3.5

# Opção B: Qwen2.5-3B (melhor qualidade, 2.0GB)
ollama pull qwen2.5

# Crie modelo custom (recomendado)
ollama create docky-phi -f ./llm/Modelfile.phi
# ou
ollama create docky-qwen -f ./llm/Modelfile.qwen
```

### 5. Inicie a API

```bash
uvicorn api.main:app --reload

# Em outro terminal, check health
curl http://localhost:8000/health
```

## 🔍 Teste os Endpoints

### SearchService (/search)

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k_initial": 15,
    "top_k_reranked": 5
  }'
```

### RAGService (/ask)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k_reranked": 5,
    "temperature": 0.3
  }'
```

### Swagger UI

Abra em seu navegador:
```
http://localhost:8000/docs
```

## 📊 Monitorar Logs

```bash
# Logs da API
docker-compose logs -f api

# Logs do Qdrant
docker-compose logs -f qdrant

# Logs do Ollama
docker-compose logs -f ollama
```

## 🧪 Rodar Testes

```bash
# Todos
pytest

# SearchService
pytest tests/unit/test_search.py -v

# RAGService
pytest tests/unit/test_rag.py -v

# Com cobertura
pytest --cov=api --cov=llm
```

## 📈 Próximos Passos

1. **Ingerir Documentação**
   - Coloque seus arquivos em `data/raw/`
   - Implemente document loaders

2. **Customizar Prompts**
   - Edit `llm/Modelfile.*` para ajustar system prompt

3. **Otimizar Retrieval**
   - Ajuste `RETRIEVAL_TOP_K` em .env
   - Fine-tune embeddings

4. **Adicionar Autenticação**
   - Implemente API key validation

---

## 🆘 Troubleshooting

### Qdrant não conecta

```bash
# Verificar status
curl http://localhost:6333/health

# Reiniciar
docker-compose restart qdrant
```

### Ollama não tem modelos

```bash
# Listar modelos
ollama list

# Baixar modelo
ollama pull phi3.5
```

### Memória insuficiente

- Use `Phi-3.5-mini` (mais leve)
- Reduza `EMBEDDING_DIMENSION`
- Reduza `RETRIEVAL_TOP_K`

---

## 📚 Documentação Completa

Ver [docs/TASKS_4_6_7_IMPLEMENTATION.md](./TASKS_4_6_7_IMPLEMENTATION.md)
