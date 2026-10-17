# Quick Start - Docky

Comece com Docky em menos de 5 minutos.

## 🏃 Início Rápido (Docker)

### 1. Setup

```bash
cd docky
cp .env.example .env
docker-compose up -d
```

### 2. Verificar

```bash
# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

### 3. Fazer Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Olá, como você funciona?"}'
```

**Pronto!** 🎉

---

## 💻 Desenvolvimento (Sem Docker)

### 1. Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Iniciar Serviços (Docker apenas)

```bash
docker-compose up -d qdrant ollama
sleep 30
```

### 3. Rodar API

```bash
uvicorn api.main:app --reload
```

API estará em: http://localhost:8000

### 4. Rodar Testes

```bash
# Quick
pytest

# Full suite
./scripts/test.sh

# Com coverage
pytest --cov
```

---

## 📚 Documentação

| Documento | Para Quem | O que faz |
|-----------|-----------|----------|
| README.md | Todos | Visão geral e setup |
| CI_CD.md | Devs | CI/CD pipeline |
| DEPLOY_VPS.md | DevOps | Deploy em VPS |
| TROUBLESHOOTING.md | Todos | Resolver problemas |
| DOCKER_COMPOSE.md | Devs | Docker reference |
| DEVELOPMENT.md | Devs | Guia desenvolvimento |

---

## 🐳 Comandos Docker Úteis

```bash
# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f api

# Parar tudo
docker-compose down

# Limpar volumes (CUIDADO!)
docker-compose down -v

# Rebuild
docker-compose build --no-cache

# Entrar em container
docker-compose exec api bash
```

---

## 🧪 Testes

```bash
# Rodar testes
pytest

# Com coverage
pytest --cov=ingest --cov=api --cov=llm

# Limpar cache
./scripts/clean.sh
```

---

## 📝 Adicionar Documentação

1. Coloque arquivos em `data/raw/`
2. API processará automaticamente
3. Consulte via `/query` endpoint

---

## 🔍 Troubleshoot

**Erro de conexão?**
```bash
# Ver logs
docker-compose logs

# Reiniciar
docker-compose restart
```

**Veja TROUBLESHOOTING.md para 20+ soluções**

---

## 🚀 Próximos Passos

- [ ] Adicionar seus documentos em `data/raw/`
- [ ] Treinar modelos
- [ ] Fazer queries
- [ ] Ver DEPLOY_VPS.md para produção

---

**Desenvolvedido por**: dev-1
**Versão**: 1.0
**Status**: ✅ Pronto para uso
