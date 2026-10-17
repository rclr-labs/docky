# CI/CD - Testes e Linting

## Visão Geral

O projeto Docky possui um pipeline completo de CI/CD com:
- **Testes automatizados**: Pytest com múltiplas versões Python
- **Linting**: Ruff, Black, isort, MyPy
- **Coverage**: Mínimo 80%
- **GitHub Actions**: Workflows automáticos

## Configuração Local

### Pré-requisitos

```bash
# Python 3.10+
python --version

# pip atualizado
pip install --upgrade pip
```

### Setup

```bash
# 1. Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# 2. (Opcional) Instalar pre-commit hooks
pip install pre-commit
pre-commit install

# 3. Rodar testes
pytest
```

## Rodando Testes Localmente

### Quick Test (pytest apenas)

```bash
pytest
```

### Full Test Suite (com linting)

```bash
./scripts/test.sh
```

Ou manualmente:

```bash
# 1. Linting com Ruff
ruff check .

# 2. Formatação com Black
black .

# 3. Type checking com MyPy
mypy ingest api llm

# 4. Testes com coverage
pytest --cov=ingest --cov=api --cov=llm --cov-report=html
```

## Configuração Pytest

Arquivo: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --strict-markers
    --cov=ingest
    --cov=api
    --cov=llm
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

### Opções Importantes

- `--cov-fail-under=80`: Falha se coverage < 80%
- `--cov-report=html`: Gera relatório HTML (abrir `htmlcov/index.html`)
- `--cov-report=xml`: Para upload em Codecov
- `-v`: Verbose output

## Configuração Ruff

Arquivo: `.ruff.toml`

```toml
[lint]
select = ["E", "F", "W", "I", "N", "UP", "ANN", "C4", "BLE", "B", "A", "COM"]
ignore = ["E501", "ANN101", "ANN102"]
line-length = 100
```

### Regras Ativadas

- **E**: PyCodeStyle errors
- **F**: Pyflakes
- **W**: PyCodeStyle warnings
- **I**: isort (import sorting)
- **N**: pep8-naming
- **UP**: pyupgrade
- **ANN**: Type hints (annotations)
- **C4**: flake8-comprehensions
- **BLE**: No bare except
- **B**: flake8-bugbear
- **A**: Avoid shadowing builtins
- **COM**: Missing trailing commas

## Configuração MyPy

Type checking de todo o código:

```bash
mypy ingest api llm --strict
```

Ignora alguns arquivos em `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

## GitHub Actions Workflows

### test.yml - Testes

Executa em:
- Python 3.10, 3.11, 3.12
- Ubuntu latest
- Em cada push para main/develop e PRs

Passos:
1. **Checkout** do código
2. **Setup Python** (com cache de pip)
3. **Install** dependências
4. **Lint** com Ruff (non-blocking)
5. **Format check** com Black (non-blocking)
6. **Type check** com MyPy (non-blocking)
7. **Run tests** com Pytest + coverage
8. **Upload** coverage para Codecov

### docker.yml - Docker Build

Executa:
- Build da imagem Docker
- Cache com GitHub Actions
- Testes da imagem

## Coverage

### Visualizar Coverage Report

```bash
# Gerar relatório HTML
pytest --cov=ingest --cov=api --cov=llm --cov-report=html

# Abrir no navegador
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Ignorar Linhas

```python
import my_module  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    main()
```

Configurado em `.coveragerc`:

```ini
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    if TYPE_CHECKING:
```

## Pre-commit Hooks

Rodar automáticamente antes de commits:

```bash
# Instalar
pre-commit install

# Rodar manualmente
pre-commit run --all-files

# Desinstalar
pre-commit uninstall
```

Configured in `.pre-commit-config.yaml`:
- Black (formatting)
- Ruff (linting + fixing)
- isort (import sorting)
- MyPy (type checking)
- Trailing whitespace
- Large files check

## Troubleshooting

### Teste falha localmente mas passa no CI

```bash
# Limpar cache
./scripts/clean.sh

# Reinstalar dependências
pip install -e ".[dev]" --force-reinstall

# Rodar testes novamente
pytest
```

### Coverage abaixo de 80%

```bash
# Ver quais linhas não têm cobertura
pytest --cov=ingest --cov=api --cov=llm --cov-report=term-missing

# Gerar relatório visual
pytest --cov=ingest --cov=api --cov=llm --cov-report=html
open htmlcov/index.html
```

### Ruff ou Black reclamam

```bash
# Deixar Ruff corrigir
ruff check . --fix

# Black formatar
black .

# isort arrumar imports
isort .
```

## Badges

Badges que aparecem no README:

- **Tests**: Status do workflow de testes
- **Docker**: Status do build Docker
- **Python**: Versões suportadas (3.10+)
- **Code Style**: Black
- **Ruff**: Conformidade com Ruff

## Recursos

- [Pytest Docs](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Ruff](https://beta.ruff.rs/)
- [Black](https://black.readthedocs.io/)
- [MyPy](https://mypy.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/actions)

---

**Última atualização**: 2024-10-17
