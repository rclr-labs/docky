# 🧪 Como Rodar os Testes: TASK #5 + E2E

## Setup Rápido

```bash
cd /Users/rafaelnc/apps/docky

# Instalar dependências (se necessário)
pip install -e ".[dev]"
```

## Rodar Testes de Compressão (TASK #5)

```bash
# Todos os testes de compressão
pytest tests/unit/test_compression.py -v

# Com cobertura
pytest tests/unit/test_compression.py --cov=api --cov-report=term-missing

# Teste específico
pytest tests/unit/test_compression.py::TestSentenceCompressor -v
```

## Rodar Testes E2E

```bash
# Todos os testes E2E
pytest tests/integration/test_e2e.py -v

# Com cobertura
pytest tests/integration/test_e2e.py --cov=api --cov=llm --cov-report=term-missing

# Teste específico
pytest tests/integration/test_e2e.py::TestE2ERAGPipeline -v
```

## Rodar Todos (Compressão + E2E)

```bash
# Quick
pytest tests/unit/test_compression.py tests/integration/test_e2e.py -v

# Com cobertura completa
pytest tests/ --cov=api --cov=llm --cov-report=html --cov-report=term-missing

# Abrir relatório HTML
open htmlcov/index.html
```

## Rodar com Pytest Markers

```bash
# Apenas testes E2E
pytest -m "asyncio" tests/integration/test_e2e.py -v

# Apenas testes unitários
pytest tests/unit/ -v
```

## Verificar Performance

```bash
# Com timing
pytest tests/unit/test_compression.py -v --durations=10

# Com output detalhado
pytest tests/unit/test_compression.py -vv -s
```

## Estatísticas

```bash
# Contar testes
pytest tests/unit/test_compression.py tests/integration/test_e2e.py --collect-only | grep "test session starts" -A 20

# Exemplo de output:
# 50 tests in compression
# 20 tests in e2e
# Total: 70 tests
```

## Troubleshooting

### Erro: "No module named 'api'"
```bash
# Instale novamente
pip install -e ".[dev]"
```

### Erro: "asyncio not installed"
```bash
# Instale pytest-asyncio
pip install pytest-asyncio
```

### Erro: "sentence_transformers not found"
```bash
# Instale sentence-transformers
pip install sentence-transformers
```

## Performance Esperada

- **Compression tests**: ~1-2 segundos (CPU-bound)
- **E2E tests**: ~1-2 segundos (com mocks, sem GPU)
- **Total**: ~2-4 segundos

---

**Nota**: Os testes E2E usam mocks do Ollama, então não precisam de GPU ou Ollama rodando.
