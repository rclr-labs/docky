#!/bin/bash
echo "🧹 Limpando cache de testes..."

# Remover cache de pytest
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -r {} + 2>/dev/null || true
find . -type d -name .mypy_cache -exec rm -r {} + 2>/dev/null || true
find . -type d -name .ruff_cache -exec rm -r {} + 2>/dev/null || true
find . -type f -name .coverage -delete 2>/dev/null || true
find . -type d -name htmlcov -exec rm -r {} + 2>/dev/null || true
find . -type f -name coverage.xml -delete 2>/dev/null || true

echo "✅ Cache limpo!"
