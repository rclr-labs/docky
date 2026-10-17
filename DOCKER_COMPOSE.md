# Docker Compose - Referência

Documentação do `docker-compose.yml` do projeto Docky.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   Docker Network                     │
│                  (docky-network)                     │
├──────────────────┬──────────────────┬───────────────┤
│   Qdrant         │   Ollama         │   API         │
│   (6333)         │   (11434)        │   (8000)      │
├──────────────────┼──────────────────┼───────────────┤
│ Vector Database  │ LLM Server       │ FastAPI       │
│ Storage Volume   │ Models Volume    │ Cache Volume  │
└──────────────────┴──────────────────┴───────────────┘
```

## Serviços

### Qdrant

**Imagem**: qdrant/qdrant:latest

**Portas**:
- 6333: HTTP REST API
- 6334: gRPC

**Volumes**:
- `qdrant_storage`: Dados de índices vectoriais
- `qdrant_snapshots`: Snapshots para backup

**Health Check**:
- Endpoint: `GET /health`
- Intervalo: 30s
- Timeout: 10s
- Retries: 5
- Start period: 40s

**Dependências**: Nenhuma

### Ollama

**Imagem**: ollama/ollama:latest

**Portas**:
- 11434: HTTP API

**Volumes**:
- `ollama_models`: LLM models baixados
- `./ollama_init.sh`: Script de inicialização (opcional)

**Health Check**:
- Endpoint: `GET /api/tags`
- Intervalo: 30s
- Timeout: 10s
- Retries: 5
- Start period: 60s (longo porque precisa puxar modelos)

**Dependências**: Nenhuma

**Nota**: Primeira inicialização pode levar alguns minutos para baixar modelos.

### API

**Imagem**: Construída do Dockerfile local

**Portas**:
- 8000: FastAPI Uvicorn

**Volumes**:
- `.:/app`: Código da aplicação (para desenvolvimento)
- `./data/raw:/data/raw`: Documentação original
- `./data/processed:/data/processed`: Documentos processados
- `api_cache`: Cache de embeddings

**Variáveis de Ambiente**:
- `API_HOST=0.0.0.0`: Bind to all interfaces
- `API_PORT=8000`: Port
- `DEBUG=false`: Modo debug (false em produção)
- `LOG_LEVEL=INFO`: Nível de logging
- `QDRANT_URL=http://qdrant:6333`: URL do Qdrant
- `OLLAMA_BASE_URL=http://ollama:11434`: URL do Ollama
- `EMBEDDING_DEVICE=cpu`: Device para embeddings

**Health Check**:
- Endpoint: `GET /health`
- Intervalo: 30s
- Timeout: 10s
- Retries: 5
- Start period: 40s

**Dependências**:
- Qdrant (service_healthy)
- Ollama (service_healthy)

### Prometheus (Opcional)

**Imagem**: prom/prometheus:latest

**Portas**:
- 9090: Web UI

**Volumes**:
- `./prometheus.yml`: Configuração
- `prometheus_data`: Dados de métricas

**Nota**: Usar `docker-compose --profile monitoring up -d` para iniciar com Prometheus.

## Volumes

| Nome | Driver | Uso |
|------|--------|-----|
| `qdrant_storage` | local | Índices vetoriais |
| `qdrant_snapshots` | local | Backups Qdrant |
| `ollama_models` | local | Modelos LLM |
| `api_cache` | local | Cache da API |
| `prometheus_data` | local | Métricas (opcional) |

## Network

**Nome**: `docky-network`

**Driver**: bridge

**Subnet**: 172.20.0.0/16

**Serviços podem comunicar usando hostnames**:
- `qdrant:6333`
- `ollama:11434`
- `api:8000`

## Logging

Cada serviço tem logging configurado:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

Previne logs de ficar muito grandes (~30MB max por serviço).

## Health Checks

Todos os serviços têm health checks para garantir disponibilidade:

```bash
# Verificar status
docker-compose ps

# Ver detalhes
docker inspect <container-name> | grep -A 10 Health
```

## Profiles

### Monitoring (Opcional)

```bash
# Iniciar com Prometheus
docker-compose --profile monitoring up -d

# Acessar: http://localhost:9090
```

## Best Practices

### Desenvolvimento

```bash
# Com reload automático
docker-compose up -d

# Ver logs
docker-compose logs -f api
```

### Produção

```bash
# Sem bind volumes
# Editar docker-compose.yml e remover volumes da API

# Rebuild
docker-compose build --no-cache

# Start
docker-compose up -d

# Verificar
docker-compose ps
docker-compose logs
```

### Performance

- Usar `network_mode: host` para máxima performance (Linux)
- Limitar recursos com `deploy.resources.limits`
- Usar restart policy: `unless-stopped`

---

**Última atualização**: 2024-10-17
