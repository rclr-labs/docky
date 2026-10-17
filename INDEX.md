# 📚 Índice de Documentação - Docky

Bem-vindo! Use este índice para navegar pela documentação do Docky.

## 🚀 Começar Rápido

Novo no Docky? Comece aqui:

1. **[QUICK_START.md](./QUICK_START.md)** ⭐
   - Setup em 5 minutos
   - Comandos essenciais
   - Primeiros passos

2. **[README.md](./README.md)**
   - Visão geral do projeto
   - Arquitetura
   - Stack tecnológico

## 💻 Desenvolvimento

Se você é desenvolvedor:

1. **[DEVELOPMENT.md](./DEVELOPMENT.md)**
   - Setup para devs
   - Convenções de código
   - TDD e debugging
   - Recursos úteis

2. **[CI_CD.md](./CI_CD.md)**
   - Setup pytest
   - Ruff linting
   - GitHub Actions
   - Pre-commit hooks
   - Coverage reporting

## 🐳 Deployment & Operações

Para deploy e produção:

1. **[DEPLOY_VPS.md](./DEPLOY_VPS.md)** 🔴 **IMPORTANTE**
   - Setup Ubuntu
   - Instalar Docker
   - Nginx reverse proxy
   - SSL/TLS com Let's Encrypt
   - Backup e restore
   - Monitoramento
   - Manutenção

2. **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** 🆘
   - Docker & containers
   - Qdrant issues
   - Ollama issues
   - API issues
   - Network issues
   - Performance tuning
   - Logs e debugging

3. **[DOCKER_COMPOSE.md](./DOCKER_COMPOSE.md)**
   - Arquitetura
   - Detalhes de cada serviço
   - Volumes
   - Network
   - Health checks
   - Profiles
   - Best practices

## 📊 Relatórios

Relatórios de implementação:

- **[TASK_8_9_FINAL_REPORT.md](./TASK_8_9_FINAL_REPORT.md)**
  - TASK #8 - CI/CD
  - TASK #9 - Deploy
  - Estatísticas
  - Checklist final

## 🗂️ Estrutura de Arquivos

```
docky/
├── 📖 Documentação (este diretório)
│   ├── README.md
│   ├── QUICK_START.md
│   ├── DEVELOPMENT.md
│   ├── CI_CD.md
│   ├── DEPLOY_VPS.md
│   ├── TROUBLESHOOTING.md
│   ├── DOCKER_COMPOSE.md
│   └── INDEX.md (este arquivo)
│
├── 🚀 Docker
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── prometheus.yml
│
├── 🧪 Testes
│   ├── pytest.ini
│   ├── .coveragerc
│   ├── .ruff.toml
│   └── tests/
│
├── ⚙️  CI/CD
│   ├── .github/workflows/test.yml
│   ├── .github/workflows/docker.yml
│   └── .pre-commit-config.yaml
│
└── 💻 Código
    ├── api/
    ├── ingest/
    ├── llm/
    └── tests/
```

## 🎯 Por Tarefa

### Setup Inicial
- [README.md](./README.md) - Visão geral
- [QUICK_START.md](./QUICK_START.md) - 5 minutos

### Desenvolvimento Local
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Setup dev
- [CI_CD.md](./CI_CD.md) - Testes locais

### Deploy em Produção
- [DEPLOY_VPS.md](./DEPLOY_VPS.md) - Passo-a-passo
- [DOCKER_COMPOSE.md](./DOCKER_COMPOSE.md) - Referência técnica

### Resolver Problemas
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - 20+ soluções

## 🔍 Buscar por Tópico

### Docker & Containers
- [DOCKER_COMPOSE.md](./DOCKER_COMPOSE.md) - Como funciona
- [DEPLOY_VPS.md](./DEPLOY_VPS.md#2-instalar-docker-e-docker-compose) - Instalar
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#docker--containers) - Problemas

### Testes & Qualidade
- [CI_CD.md](./CI_CD.md#configuração-pytest) - Setup pytest
- [CI_CD.md](./CI_CD.md#configuração-ruff) - Ruff linting
- [DEVELOPMENT.md](./DEVELOPMENT.md#testes) - Rodando testes

### GitHub Actions
- [CI_CD.md](./CI_CD.md#github-actions-workflows) - Como funciona
- [CI_CD.md](./CI_CD.md#badges) - Badges

### Nginx & SSL
- [DEPLOY_VPS.md](./DEPLOY_VPS.md#5-nginx-reverse-proxy) - Configurar
- [DEPLOY_VPS.md](./DEPLOY_VPS.md#53-ssl-com-lets-encrypt) - SSL

### Monitoramento
- [DOCKER_COMPOSE.md](./DOCKER_COMPOSE.md#prometheus-opcional) - Prometheus
- [DEPLOY_VPS.md](./DEPLOY_VPS.md#6-monitoramento) - Logs e métricas

### Backup
- [DEPLOY_VPS.md](./DEPLOY_VPS.md#7-backup-e-restore) - Backup/restore

## ❓ FAQs Rápidas

**P: Como rodar testes?**
A: `pytest` ou `./scripts/test.sh`
Veja: [CI_CD.md](./CI_CD.md#rodando-testes-localmente)

**P: Docker não funciona?**
A: Veja: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#docker--containers)

**P: Como fazer deploy em VPS?**
A: Veja: [DEPLOY_VPS.md](./DEPLOY_VPS.md)

**P: Qual é a arquitetura?**
A: Veja: [README.md](./README.md#arquitetura) ou [DOCKER_COMPOSE.md](./DOCKER_COMPOSE.md#arquitetura)

**P: Qdrant ou Ollama não responde?**
A: Veja: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## 📞 Links Úteis

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Ollama Docs](https://github.com/ollama/ollama)
- [Docker Docs](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/actions)

## 📊 Estatísticas

| Métrica | Valor |
|---------|-------|
| Documentação | 8 arquivos, 2500+ linhas |
| Código | 600+ linhas Python |
| Testes | 16 testes unitários |
| CI/CD | 2 workflows GitHub Actions |
| Deploy | Docker Compose + VPS guide |
| Commits | 39 total |

## ✨ Destaques

🌟 **Bem Documentado** - Cada feature tem documentação
🌟 **Pronto para Produção** - VPS guide completo
🌟 **Troubleshooting** - 20+ soluções de problemas
🌟 **Fácil de Começar** - QUICK_START em 5 minutos
🌟 **CI/CD Automático** - GitHub Actions configurado
🌟 **Type Safe** - 100% type hints
🌟 **Testável** - pytest com coverage > 80%

## 🎓 Aprender Mais

1. Comece com [QUICK_START.md](./QUICK_START.md)
2. Leia [README.md](./README.md) para entender a arquitetura
3. Se desenvolver, use [DEVELOPMENT.md](./DEVELOPMENT.md)
4. Para deploy, siga [DEPLOY_VPS.md](./DEPLOY_VPS.md)
5. Com problemas? Consulte [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## 📝 Notas

- Todos os arquivos estão em Markdown
- Código está em Python 3.10+
- Docker é recomendado para produção
- Contribuições bem-vindas!

---

**Última atualização**: 2024-10-17
**Versão**: 1.0
**Status**: ✅ Documentação Completa
