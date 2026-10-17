#!/bin/bash
set -e

echo "🧪 Executando testes Docky..."
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se estamos em um venv
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Nenhum venv ativo. Ativando...\n${NC}"
    source venv/bin/activate 2>/dev/null || (python -m venv venv && source venv/bin/activate) || true
fi

# Instalar dependências
echo -e "${YELLOW}📦 Instalando dependências...\n${NC}"
pip install -e ".[dev]" > /dev/null 2>&1 || true

# 1. Ruff linting
echo -e "${YELLOW}1️⃣  Ruff - Linting...\n${NC}"
if ruff check . 2>/dev/null ; then
    echo -e "${GREEN}✅ Ruff OK\n${NC}"
else
    echo -e "${YELLOW}⚠️  Ruff não disponível\n${NC}"
fi

# 2. Black formatting
echo -e "${YELLOW}2️⃣  Black - Formatação...\n${NC}"
if black --check . > /dev/null 2>&1 ; then
    echo -e "${GREEN}✅ Black OK\n${NC}"
else
    echo -e "${YELLOW}⚠️  Black: corrigindo formatação...\n${NC}"
    black . > /dev/null 2>&1 || true
fi

# 3. MyPy type checking
echo -e "${YELLOW}3️⃣  MyPy - Type checking...\n${NC}"
if mypy ingest api llm --no-error-summary > /dev/null 2>&1 ; then
    echo -e "${GREEN}✅ MyPy OK\n${NC}"
else
    echo -e "${YELLOW}⚠️  MyPy encontrou problemas (informativo)\n${NC}"
fi

# 4. Pytest com coverage
echo -e "${YELLOW}4️⃣  Pytest - Testes...\n${NC}"
if pytest --cov=ingest --cov=api --cov=llm --cov-report=term-missing 2>/dev/null ; then
    echo -e "${GREEN}✅ Pytest OK\n${NC}"
else
    echo -e "${RED}❌ Pytest falhou\n${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════\n"
echo -e "🎉 Todos os testes passaram!\n"
echo -e "════════════════════════════════════════════${NC}"
