# Troubleshooting - Docky

Guia para resolver problemas comuns com Docky.

## Docker & Containers

### Problema: "Cannot connect to Docker daemon"

**Causa**: Docker não está rodando

**Solução**:
```bash
# Verificar status
sudo systemctl status docker

# Iniciar Docker
sudo systemctl start docker

# Iniciar no boot (opcional)
sudo systemctl enable docker
```

### Problema: "docker-compose: command not found"

**Causa**: docker-compose não está instalado ou PATH incorreto

**Solução**:
```bash
# Verificar instalação
which docker-compose

# Se não encontrar
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar
docker-compose --version
```

### Problema: "Permission denied while trying to connect to Docker"

**Causa**: Usuário não está no grupo docker

**Solução**:
```bash
# Adicionar ao grupo
sudo usermod -aG docker $USER
newgrp docker

# Ou use sudo
sudo docker-compose up -d
```

### Problema: "Cannot assign requested address"

**Causa**: Porta já está em uso

**Solução**:
```bash
# Verificar qual processo usa a porta
sudo lsof -i :8000
sudo lsof -i :6333
sudo lsof -i :11434

# Parar o processo
sudo kill -9 <PID>

# Ou usar porta diferente em docker-compose.yml
# Alterar "8000:8000" para "8001:8000" por exemplo
```

### Problema: "no space left on device"

**Causa**: Disco cheio

**Solução**:
```bash
# Ver espaço disponível
df -h

# Ver uso por container
docker system df

# Limpar imagens não usadas
docker image prune -a

# Limpar volumes não usados
docker volume prune

# Limpar tudo (CUIDADO!)
docker system prune -a

# Se problema é com logs, limpar logs dos containers
# Editar /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Qdrant

### Problema: "Qdrant health check failing"

**Logs**:
```bash
docker-compose logs qdrant
```

**Causas e soluções**:

1. **Qdrant não está respondendo**
   ```bash
   # Verificar se está rodando
   docker-compose ps
   
   # Restart
   docker-compose restart qdrant
   ```

2. **Porta 6333 bloqueada**
   ```bash
   # Verificar porta
   sudo netstat -tlnp | grep 6333
   
   # Liberar firewall
   sudo ufw allow 6333
   ```

3. **Volume corrupto**
   ```bash
   # Remover volume
   docker volume rm docky_qdrant_storage
   
   # Restart (recria volume vazio)
   docker-compose up -d qdrant
   ```

### Problema: "Could not find Qdrant collection"

**Causa**: Collection não foi criada

**Solução**:
```bash
# Verificar collections
curl http://localhost:6333/collections

# Se vazio, documentos não foram ingeridos ainda
# Ver INGEST.md para adicionar documentos
```

### Problema: "Qdrant taking too much memory"

**Solução**:
```bash
# Verificar tamanho
docker exec docky-qdrant du -sh /qdrant/storage

# Se muito grande, pode ser normal para muitos documentos
# Ou pode precisar fazer snapshot e compress

# Fazer snapshot
curl -X POST http://localhost:6333/snapshots
```

## Ollama

### Problema: "Ollama health check failing"

**Logs**:
```bash
docker-compose logs ollama
```

**Causas e soluções**:

1. **Ollama está lento**
   ```bash
   # Pode ser lento na primeira execução
   # Aguardar 60+ segundos
   
   # Aumentar start_period em docker-compose.yml
   docker-compose logs -f ollama
   ```

2. **Modelo não está carregado**
   ```bash
   # Verificar modelos disponíveis
   curl http://localhost:11434/api/tags
   
   # Puxar modelo
   docker exec docky-ollama ollama pull mistral
   ```

3. **Porta 11434 bloqueada**
   ```bash
   sudo ufw allow 11434
   ```

### Problema: "Generating very slow"

**Causas**: Falta de VRAM, modelo pesado, CPU lenta

**Soluções**:

1. **Usar modelo mais leve**
   ```bash
   docker exec docky-ollama ollama pull phi
   # ou
   docker exec docky-ollama ollama pull neural-chat
   ```

2. **Verificar se está usando GPU** (em máquinas com NVIDIA)
   ```bash
   # Dentro do container
   docker exec docky-ollama nvidia-smi
   
   # Se não aparecer, GPU não está disponível
   # Ver Dockerfile para passar --gpus all
   ```

3. **Aumentar timeout**
   ```bash
   # Em .env
   OLLAMA_TIMEOUT=120
   ```

### Problema: "Model not found"

```bash
# Listar modelos disponíveis
curl http://localhost:11434/api/tags

# Puxar modelo
docker exec docky-ollama ollama pull <model-name>

# Modelos leves recomendados:
# - phi (2.7B)
# - neural-chat (7B)
# - mistral (7B)
# - qwen2.5-7b
```

## API FastAPI

### Problema: "API container keeps restarting"

**Logs**:
```bash
docker-compose logs -f api
```

**Causas**:

1. **Importação falha**
   - Verificar erros de sintaxe Python
   - Reinstalar dependências: `pip install -e ".[dev]"`

2. **Porta em uso**
   - Ver seção "Cannot assign requested address" acima

3. **Memória insuficiente**
   ```bash
   # Ver uso
   docker stats
   
   # Aumentar limite em docker-compose.yml
   # deploy:
   #   resources:
   #     limits:
   #       memory: 1G
   ```

### Problema: "ModuleNotFoundError"

**Solução**:
```bash
# Reinstalar
docker-compose build --no-cache api
docker-compose up -d api
```

### Problema: "Connection refused to Qdrant/Ollama"

**Causas**: Serviços não estão prontos quando API inicia

**Solução**:
```bash
# Verificar depends_on em docker-compose.yml (já configurado)

# Se ainda falhar, usar delay manual
docker-compose up -d qdrant ollama
sleep 30
docker-compose up -d api
```

### Problema: "Timeout connecting to Qdrant"

**Logs**:
```bash
docker-compose logs api | grep -i qdrant
```

**Solução**:
```bash
# Aumentar timeout em api/config.py
QDRANT_TIMEOUT = 30  # padrão 10

# Ou verificar se Qdrant está respondendo
curl http://qdrant:6333/health
```

## Network & Conectividade

### Problema: "Cannot reach API from localhost:8000"

**Verificar**:
```bash
# Ver se container está rodando
docker-compose ps

# Ver logs
docker-compose logs api

# Testar de dentro do container
docker exec docky-api curl http://localhost:8000/health

# Testar do host
curl http://localhost:8000/health

# Testar IP específico
curl http://0.0.0.0:8000/health
```

### Problema: "Cannot reach API from outro servidor"

**Causas**: Firewall, bind correto

**Soluções**:
```bash
# Liberar porta no firewall
sudo ufw allow 8000

# Ou verificar iptables
sudo iptables -L -n | grep 8000

# Verificar se está bindeado em 0.0.0.0
docker-compose logs api | grep "Uvicorn running"
```

## Performance

### Slow Response Times

**Diagnóstico**:
```bash
# Ver recursos
docker stats

# Ver logs de query
docker-compose logs -f api | grep query

# Profile de um request
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

**Otimizações**:

1. **Cache**
   ```bash
   # Ativar em .env
   ENABLE_CACHE=true
   CACHE_TTL_SECONDS=3600
   ```

2. **Re-ranking desabilitado**
   ```bash
   ENABLE_RERANKING=false
   ```

3. **Reduzir TOP_K**
   ```bash
   RETRIEVAL_TOP_K=3  # de 5 para 3
   ```

## Logs

### Ver logs de um serviço

```bash
# Últimas linhas
docker-compose logs --tail=100 <service>

# Em tempo real
docker-compose logs -f <service>

# Tudo
docker-compose logs

# Com timestamps
docker-compose logs --timestamps
```

### Logs de erro específico

```bash
# Grep nos logs
docker-compose logs api | grep ERROR

# Salvar em arquivo
docker-compose logs > logs.txt
```

## Database

### Problema: "Cannot connect to database"

```bash
# Se usar SQLite
ls -la docky.db

# Se vazio, pode ser permissão
chmod 666 docky.db
```

## Resetar Tudo

### Quando nada mais funciona

```bash
# Parar tudo
docker-compose down -v  # -v remove volumes!

# Limpar cache Python
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true

# Fazer rebuild
docker-compose build --no-cache

# Iniciar fresco
docker-compose up -d

# Verificar
docker-compose ps
```

## Support

Se o problema persistir:

1. Verificar logs: `docker-compose logs`
2. Consultar documentação de cada serviço
3. Abrir issue no GitHub
4. Descrever: OS, versão Docker, logs completos, passos para reproduzir

---

**Última atualização**: 2024-10-17
