# Deploy em VPS - Guia Completo

## Visão Geral

Guia passo a passo para deploy do Docky em uma VPS (Virtual Private Server) com Docker.

### Pré-requisitos

- VPS com mínimo 2GB RAM, 20GB SSD
- Ubuntu 20.04 LTS ou superior
- SSH access
- Domínio (opcional)

## 1. Setup Inicial da VPS

### 1.1 Conexão SSH

```bash
ssh root@seu-vps-ip
```

### 1.2 Atualizar Sistema

```bash
apt update && apt upgrade -y
apt install -y curl wget git htop nano
```

### 1.3 Criar Usuário Não-Root

```bash
# Criar usuário
adduser docky

# Adicionar ao sudo
usermod -aG sudo docky

# Trocar para novo usuário
su - docky
```

## 2. Instalar Docker e Docker Compose

### 2.1 Instalar Docker

```bash
# Instalar dependências
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Adicionar chave GPG Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repo Docker
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker docky
newgrp docker

# Verificar instalação
docker --version
docker run hello-world
```

### 2.2 Instalar Docker Compose (standalone)

```bash
# Baixar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Tornar executável
sudo chmod +x /usr/local/bin/docker-compose

# Verificar
docker-compose --version
```

### 2.3 Iniciar Docker no Boot

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

## 3. Clone e Setup do Docky

### 3.1 Clonar Repositório

```bash
cd /home/docky
git clone https://github.com/rafaelnc/docky.git
cd docky
```

### 3.2 Configurar Variáveis de Ambiente

```bash
# Copiar exemplo
cp .env.example .env

# Editar com suas configurações
nano .env
```

**Variáveis importantes para VPS:**

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=seu-api-key-seguro

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral

# Ingestão
INGEST_SOURCE_DIR=/data/raw
INGEST_PROCESSED_DIR=/data/processed
INGEST_MAX_FILE_SIZE_MB=100

# RAG
RETRIEVAL_TOP_K=5
ENABLE_RERANKING=true
```

### 3.3 Criar Diretórios de Dados

```bash
# Criar diretórios com permissões corretas
mkdir -p data/raw data/processed
chmod -R 755 data/

# Criar arquivo de inicialização Ollama (opcional)
cat > ollama_init.sh << 'EOF'
#!/bin/bash
echo "Puxando modelo Ollama..."
ollama pull mistral
echo "Modelo pronto!"
EOF
chmod +x ollama_init.sh
```

## 4. Iniciar Serviços

### 4.1 Build e Start

```bash
# Build da imagem
docker-compose build

# Iniciar em background
docker-compose up -d

# Verificar status
docker-compose ps
```

### 4.2 Verificar Health

```bash
# Ver logs
docker-compose logs -f

# Health check individual
curl http://localhost:6333/health  # Qdrant
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/health  # API
```

## 5. Nginx Reverse Proxy (Recomendado)

### 5.1 Instalar Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 5.2 Configurar Reverse Proxy

Criar `/etc/nginx/sites-available/docky`:

```nginx
upstream docky_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;

    # SSL Certificate (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    # SSL Config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logs
    access_log /var/log/nginx/docky_access.log;
    error_log /var/log/nginx/docky_error.log;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req zone=general burst=20 nodelay;

    # Proxy
    location / {
        proxy_pass http://docky_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para operações longas
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Swagger/Docs
    location /docs {
        proxy_pass http://docky_api/docs;
    }

    # Healthcheck
    location /health {
        proxy_pass http://docky_api/health;
        access_log off;
    }
}
```

Ativar:

```bash
# Criar symlink
sudo ln -s /etc/nginx/sites-available/docky /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar
sudo systemctl reload nginx
```

### 5.3 SSL com Let's Encrypt

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Gerar certificado
sudo certbot certonly --standalone -d seu-dominio.com -d www.seu-dominio.com

# Renovação automática
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## 6. Monitoramento

### 6.1 Logs dos Serviços

```bash
# Ver logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs -f api
docker-compose logs -f qdrant
docker-compose logs -f ollama

# Últimas 100 linhas
docker-compose logs --tail=100 api
```

### 6.2 CPU e Memória

```bash
# Stats dos containers
docker stats

# Detalhado
docker-compose stats
```

### 6.3 Disk Space

```bash
# Verificar espaço em disco
df -h

# Usar por serviço
du -sh /home/docky/data/*
```

## 7. Backup e Restore

### 7.1 Backup de Dados

```bash
# Backup Qdrant
docker exec docky-qdrant tar czf /tmp/qdrant_backup.tar.gz /qdrant/storage
docker cp docky-qdrant:/tmp/qdrant_backup.tar.gz ./

# Backup Ollama models
docker cp docky-ollama:/root/.ollama ./ollama_backup

# Backup dados aplicação
tar czf app_backup.tar.gz data/
```

### 7.2 Restore

```bash
# Restore Qdrant
docker cp qdrant_backup.tar.gz docky-qdrant:/tmp/
docker exec docky-qdrant tar xzf /tmp/qdrant_backup.tar.gz -C /

# Restart
docker-compose restart qdrant
```

## 8. Atualizações

### 8.1 Atualizar Imagens

```bash
# Pull imagens mais recentes
docker-compose pull

# Rebuild
docker-compose build --no-cache

# Restart
docker-compose down
docker-compose up -d
```

### 8.2 Atualizar Código

```bash
cd /home/docky/docky
git pull origin main
docker-compose up -d --build
```

## 9. Manutenção

### 9.1 Limpeza de Imagens

```bash
# Remover imagens não usadas
docker image prune -a

# Remover volumes não usados
docker volume prune

# Remover tudo (CUIDADO!)
docker system prune -a
```

### 9.2 Cron para Backups Automáticos

Criar `/home/docky/backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/docky

mkdir -p $BACKUP_DIR

# Backup Qdrant
docker exec docky-qdrant tar czf /tmp/qdrant_$DATE.tar.gz /qdrant/storage
docker cp docky-qdrant:/tmp/qdrant_$DATE.tar.gz $BACKUP_DIR/

# Backup dados
cd /home/docky/docky
tar czf $BACKUP_DIR/app_$DATE.tar.gz data/

# Manter últimos 7 dias
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup $DATE completed"
```

Adicionar ao crontab:

```bash
crontab -e
# Adicionar linha (backup diário às 2:00 AM)
0 2 * * * /home/docky/backup.sh
```

## Troubleshooting

Ver `TROUBLESHOOTING.md` para problemas comuns.

## Segurança

### Checklist de Segurança

- [ ] Alterar QDRANT_API_KEY
- [ ] Usar HTTPS com Let's Encrypt
- [ ] Firewall configurado
- [ ] Backups automáticos
- [ ] Logs monitorados
- [ ] Docker images atualizadas

---

**Última atualização**: 2024-10-17
