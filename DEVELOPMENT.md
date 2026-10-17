# Guia de Desenvolvimento - Docky

Este documento descreve a arquitetura técnica e procedimentos de desenvolvimento do projeto Docky.

## Arquitetura

### Componentes

1. **API (FastAPI)** - `api/`
   - Router principal
   - Configurações
   - Health checks
   - Validação com Pydantic

2. **Ingestão de Documentos** - `ingest/`
   - Document loaders (TXT, MD, PDF, Docx)
   - Processamento e chunking
   - Persistência em Qdrant

3. **Clients LLM** - `llm/`
   - Cliente Ollama
   - Cliente de Embeddings
   - Cache de resultados

4. **Vector DB** - Qdrant (via Docker)
   - Armazena embeddings
   - Busca por similaridade

5. **LLM Local** - Ollama (via Docker)
   - Inferência local
   - Modelos: Mistral, Phi, Qwen

### Fluxo de Dados

```
[Documento] → [Loader] → [Chunking] → [Embeddings] → [Qdrant]
                                          ↓
[Query] → [Embeddings] → [Busca Qdrant] → [Re-rank] → [LLM] → [Resposta]
```

## Setup para Desenvolvedores

### 1. Clonar e preparar

```bash
git clone https://github.com/rafaelnc/docky.git
cd docky
python -m venv venv
source venv/bin/activate  # ou: venv\Scripts\activate (Windows)
pip install -e ".[dev]"
cp .env.example .env
```

### 2. Iniciar serviços (Docker)

```bash
# Terminal 1: Qdrant + Ollama
docker-compose up -d qdrant ollama

# Aguardar que estejam saudáveis
sleep 10

# Terminal 2: API em desenvolvimento
uvicorn api.main:app --reload --port 8000

# Terminal 3: Puxar modelo Ollama
ollama pull mistral
```

### 3. Verificar saúde

```bash
# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

## Convenções de Código

### Estilo

- **Python 3.10+**: Type hints obrigatórias
- **Black**: Formatação (100 caracteres por linha)
- **Ruff**: Linting
- **MyPy**: Type checking

### Configurar hooks pré-commit (opcional mas recomendado)

```bash
# Instalar pre-commit
pip install pre-commit

# Criar arquivo .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.0.292
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
EOF

# Instalar hooks
pre-commit install
```

## Estrutura de Testes

```
tests/
├── unit/           # Testes unitários (rápidos, sem I/O)
└── integration/    # Testes de integração (com serviços reais)
```

### Executar testes

```bash
# Todos
pytest

# Com cobertura
pytest --cov=ingest --cov=api --cov=llm

# Específicos
pytest tests/unit/test_api.py -v

# Watch mode (requer pytest-watch)
ptw
```

## Adicionar nova feature

### 1. Criar branch

```bash
git checkout -b feat/minha-feature
```

### 2. Desenvolver (TDD recomendado)

```bash
# 1. Criar teste
echo 'def test_nova_feature(): ...' >> tests/unit/test_nova_feature.py

# 2. Executar (deve falhar)
pytest tests/unit/test_nova_feature.py

# 3. Implementar
# ... editar código ...

# 4. Executar testes (devem passar)
pytest tests/unit/test_nova_feature.py

# 5. Validar qualidade
black .
ruff check . --fix
mypy ingest api llm
```

### 3. Commit e Push

```bash
git add -A
git commit -m "feat: descrever mudança"
git push origin feat/minha-feature
```

## Criar novo module/package

### Exemplo: Novo loader para formato X

```bash
# 1. Criar arquivo
touch ingest/loaders/format_x_loader.py

# 2. Implementar interface BaseLoader
cat > ingest/loaders/format_x_loader.py << 'EOF'
from ingest.loader import BaseLoader, Document, DocumentMetadata

class FormatXLoader(BaseLoader):
    async def load(self, file_path: str) -> Document:
        # Implementar lógica
        pass
    
    async def validate(self, file_path: str) -> bool:
        return file_path.endswith('.x')
EOF

# 3. Registrar no factory
# ... editar ingest/loader.py ...

# 4. Criar teste
touch tests/unit/test_format_x_loader.py

# 5. Testar
pytest tests/unit/test_format_x_loader.py
```

## Debugging

### Logs

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Mensagem de debug")
logger.info("Informação")
logger.warning("Aviso")
logger.error("Erro")
```

### Variáveis de ambiente para debug

```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
uvicorn api.main:app --reload
```

### Debugger (VSCode)

Criar `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "api.main:app",
        "--reload",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

## Performance

### Profiling

```bash
# Instalar
pip install py-spy

# Usar
py-spy record -o profile.svg -- uvicorn api.main:app
```

### Benchmarking

```bash
# Instalar
pip install pytest-benchmark

# Criar teste
cat > tests/unit/test_performance.py << 'EOF'
def test_query_performance(benchmark):
    def run_query():
        # Query code here
        pass
    
    benchmark(run_query)
EOF
```

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'docky'"

```bash
# Reinstalar em modo desenvolvimento
pip install -e .
```

### Erro: "Connection refused" (Qdrant/Ollama)

```bash
# Verificar se estão rodando
docker ps | grep -E "qdrant|ollama"

# Reiniciar
docker-compose restart qdrant ollama
```

### Erro: "Model not found" (Ollama)

```bash
# Puxar modelo
ollama pull mistral

# Listar modelos
ollama list
```

## CI/CD

### GitHub Actions (planejado)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest
      - run: ruff check .
      - run: mypy ingest api llm
```

## Deploy

### Produção (VPS)

```bash
# 1. SSH
ssh user@vps.example.com

# 2. Clone e setup
git clone https://github.com/rafaelnc/docky.git
cd docky
docker-compose up -d

# 3. Nginx reverse proxy
# ... configurar ...

# 4. SSL
# ... certbot ...
```

## Documentação

- Adicionar docstrings em todas as funções (formato Google ou NumPy)
- Manter README.md atualizado
- Documentar decisões arquiteturais em `docs/adr/`

## Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Ollama Docs](https://github.com/ollama/ollama)

---

**Última atualização**: 2024-10-17
