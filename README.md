# Docky

Chatbot de documentação com RAG otimizado para baixo consumo de tokens, rodando em VPS com modelo LLM local pequeno.

## Visão geral

Docky responde perguntas sobre a documentação de uma aplicação (markdown, specs de API, código-fonte,
tabelas, PDFs, diagramas e transcrições) usando um pipeline de RAG (Retrieval-Augmented Generation)
desenhado para minimizar tokens em cada etapa — da indexação à resposta final.

## Arquitetura

```
Pergunta do usuário
   │
   ▼
[Roteamento por tipo de dado]   (filtro de metadados antes da busca vetorial)
   │
   ▼
[Busca vetorial: top 15-20]      (Qdrant + bge-small-en-v1.5)
   │
   ▼
[Re-rank → top 3-5]              (bge-reranker-base, local)
   │
   ▼
[Compressão extrativa]           (reduz cada chunk ao trecho relevante)
   │
   ▼
[Prompt compacto + cache de prefixo]
   │
   ▼
[LLM local pequeno]  (Phi-3.5-mini / Qwen2.5-3B via Ollama) → resposta
```

## Stack

- **Orquestração**: LlamaIndex (Python)
- **Vector DB**: Qdrant
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Re-rank**: Integrado com LlamaIndex
- **LLM**: Mistral, Phi ou Qwen, servido via Ollama
- **Backend**: FastAPI + Uvicorn
- **Deploy**: Docker Compose

## Estrutura de pastas

```
docky/
├── ingest/              # Pipeline de ingestão por tipo de dado
│   ├── __init__.py
│   └── loader.py        # Document loaders base
├── api/                 # Backend FastAPI
│   ├── __init__.py
│   ├── main.py          # Aplicação principal
│   ├── config.py        # Configurações
│   └── health.py        # Health check endpoints
├── llm/                 # Clientes para LLM e embeddings
│   ├── __init__.py
│   └── client.py        # Clientes Ollama e embeddings
├── data/
│   ├── raw/             # Documentação original (entrada)
│   └── processed/       # Chunks processados
├── tests/               # Testes automatizados
│   ├── unit/
│   └── integration/
├── docs/                # Documentação do projeto (ADRs, decisões)
├── pyproject.toml       # Dependências do projeto
├── Dockerfile           # Imagem Docker otimizada
├── docker-compose.yml   # Stack: API + Qdrant + Ollama
├── .env.example         # Variáveis de ambiente (exemplo)
└── README.md            # Este arquivo
```

## Setup Local

### Pré-requisitos

- Python 3.10+
- Docker & Docker Compose
- Git

### Instalação Rápida (com Docker)

```bash
# 1. Clone o repositório
git clone https://github.com/rafaelnc/docky.git
cd docky

# 2. Configure variáveis de ambiente
cp .env.example .env

# 3. Inicie os serviços com Docker Compose
docker-compose up -d

# 4. Verifique a saúde dos serviços
curl http://localhost:8000/health

# 5. Acesse a API
# Swagger: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Instalação Local (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/rafaelnc/docky.git
cd docky

# 2. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Em Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -e ".[dev]"

# 4. Configure variáveis de ambiente
cp .env.example .env

# 5. Inicie Qdrant e Ollama localmente
# Opção A: Com Docker (apenas os serviços, não a API)
docker-compose up -d qdrant ollama

# Opção B: Instale manualmente
# - Qdrant: https://qdrant.tech/documentation/quick-start/
# - Ollama: https://ollama.ai/

# 6. Inicie o servidor de desenvolvimento
uvicorn api.main:app --reload

# 7. Em outro terminal, puxe um modelo Ollama
ollama pull mistral  # ou outro modelo

# 8. Acesse a API
# Swagger: http://localhost:8000/docs
# API: http://localhost:8000
```

## Tipos de dados suportados

- ✅ Markdown/texto (guias, tutoriais, FAQs)
- 🚧 Especificação de API (OpenAPI/Swagger)
- 🚧 Código-fonte / docstrings
- 🚧 Tabelas estruturadas (CSV, planilhas)
- 🚧 PDFs
- 🚧 Imagens/diagramas (via legenda gerada por vision LLM)
- 🚧 Transcrições (vídeo/áudio)

## Primeiros passos com a API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Enviar uma Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "O que é Docky?"}'
```

### 3. Ingerir Documentação

Adicione seus arquivos em `data/raw/` e a API processará automaticamente.

```bash
# Coloque seus documentos em data/raw/
cp ~/docs/*.md data/raw/

# A API detectará e processará os arquivos
```

## Desenvolvimento

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=ingest --cov=api --cov=llm

# Testes específicos
pytest tests/unit/test_api.py
```

### Linting e Formatação

```bash
# Verificar estilo
ruff check .

# Formatar código
black .

# Type checking
mypy ingest api llm
```

### Adicionar Dependências

```bash
# Edite pyproject.toml e instale
pip install -e ".[dev]"
```

## Configuração

Ver `.env.example` para todas as variáveis disponíveis:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `API_PORT` | 8000 | Porta do servidor |
| `DEBUG` | False | Modo debug |
| `QDRANT_URL` | http://qdrant:6333 | URL do Qdrant |
| `OLLAMA_BASE_URL` | http://ollama:11434 | URL do Ollama |
| `OLLAMA_MODEL` | mistral | Modelo padrão |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Modelo de embeddings |
| `RETRIEVAL_TOP_K` | 5 | Documentos a recuperar |
| `RETRIEVAL_SIMILARITY_THRESHOLD` | 0.5 | Threshold de similaridade |

## Troubleshooting

### Qdrant não está respondendo

```bash
# Verificar se está rodando
curl http://localhost:6333/health

# Reiniciar container
docker-compose restart qdrant
```

### Ollama não tem modelos

```bash
# Puxar um modelo
ollama pull mistral

# Listar modelos disponíveis
ollama list
```

### Dependências não instalarem

```bash
# Atualizar pip
pip install --upgrade pip

# Reinstalar com verbose
pip install -e ".[dev]" -v
```

## Status

🚧 Projeto em fase inicial de estruturação. Em desenvolvimento via software factory.

### Checklist de Implementação

- [x] Estrutura base do projeto
- [x] Configuração de dependências (pyproject.toml)
- [x] Docker & Docker Compose
- [x] API FastAPI básica
- [x] Health checks
- [ ] Document loaders (PDF, Docx)
- [ ] Integração com LlamaIndex
- [ ] Integração com Qdrant
- [ ] Pipeline de ingestão completo
- [ ] Endpoints de busca e query
- [ ] Testes de integração
- [ ] Documentação completa
- [ ] CI/CD pipeline

## Contribuindo

Ver `docs/CONTRIBUTING.md` para guidelines.

## Licença

MIT
