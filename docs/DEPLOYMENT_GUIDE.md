# Super Manager - Deployment Guide

## Overview

This guide covers deploying Super Manager to production environments including cloud platforms, containerized environments, and self-hosted setups.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployments](#cloud-deployments)
5. [Database Setup](#database-setup)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup Configuration](#backup-configuration)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** 20.10+ & Docker Compose 2.0+
- **Node.js** 20.x LTS (for frontend builds)
- **Python** 3.11+ (for backend)
- **PostgreSQL** 15+ (or Supabase account)

### API Keys Required

| Service | Environment Variable | Purpose |
|---------|---------------------|---------|
| Groq | `GROQ_API_KEY` | AI/LLM processing |
| Supabase | `SUPABASE_URL`, `SUPABASE_KEY` | Database |
| Telegram | `TELEGRAM_BOT_TOKEN` | Notifications |
| SMTP | `SMTP_EMAIL`, `SMTP_PASSWORD` | Email sending |

---

## Environment Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Required Variables

```env
# =============================================================================
# Super Manager - Production Environment Configuration
# =============================================================================

# Application
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-min-32-chars
PORT=8000

# AI/LLM
GROQ_API_KEY=gsk_your_groq_api_key

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Cache (Redis)
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
RATE_LIMIT_PER_MINUTE=100
```

---

## Docker Deployment

### Quick Start

```bash
# Build and run all services
docker compose up -d

# View logs
docker compose logs -f backend

# Check status
docker compose ps
```

### Production Build

```bash
# Build production images
docker compose -f docker-compose.yml build

# Run with production settings
docker compose -f docker-compose.yml up -d

# Scale backend workers
docker compose up -d --scale backend=3
```

### Docker Commands Reference

```bash
# Rebuild without cache
docker compose build --no-cache

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# View service logs
docker compose logs -f [service-name]

# Execute command in container
docker compose exec backend python -m pytest

# Check container health
docker compose ps
```

---

## Cloud Deployments

### Render.com (Current Production)

1. **Connect Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - New → Web Service
   - Connect your GitHub repository

2. **Configure Service**
   ```yaml
   Name: super-manager-api
   Environment: Docker
   Region: Oregon (or nearest)
   Branch: main
   Plan: Starter ($7/mo) or higher
   ```

3. **Environment Variables**
   - Add all variables from `.env`
   - Set `PORT=10000` (Render uses this)

4. **Deploy**
   - Render auto-deploys on push to main
   - Manual deploy: Dashboard → Manual Deploy

### Vercel (Frontend)

1. **Import Project**
   ```bash
   cd frontend
   vercel
   ```

2. **Configure Build**
   ```json
   {
     "buildCommand": "npm run build",
     "outputDirectory": "dist",
     "installCommand": "npm install"
   }
   ```

3. **Environment Variables**
   ```
   VITE_API_URL=https://super-manager-api.onrender.com
   ```

### AWS (ECS/Fargate)

1. **Push to ECR**
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
   docker build -t super-manager .
   docker tag super-manager:latest $ECR_URI:latest
   docker push $ECR_URI:latest
   ```

2. **Create Task Definition**
   ```json
   {
     "family": "super-manager",
     "containerDefinitions": [{
       "name": "backend",
       "image": "${ECR_URI}:latest",
       "portMappings": [{"containerPort": 8000}],
       "environment": [
         {"name": "APP_ENV", "value": "production"}
       ],
       "secrets": [
         {"name": "GROQ_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
       ]
     }]
   }
   ```

3. **Create Service**
   ```bash
   aws ecs create-service \
     --cluster super-manager \
     --service-name backend \
     --task-definition super-manager \
     --desired-count 2 \
     --launch-type FARGATE
   ```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/super-manager

# Deploy
gcloud run deploy super-manager \
  --image gcr.io/PROJECT_ID/super-manager \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Database Setup

### Supabase (Recommended)

1. Create project at [supabase.com](https://supabase.com)
2. Get connection details from Settings → Database
3. Run migrations:
   ```bash
   psql $DATABASE_URL < backend/migrations/001_initial_schema.sql
   ```

### Self-Hosted PostgreSQL

```bash
# Docker
docker run -d \
  --name postgres \
  -e POSTGRES_USER=supermanager \
  -e POSTGRES_PASSWORD=your-password \
  -e POSTGRES_DB=supermanager \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:15-alpine

# Run migrations
docker exec -i postgres psql -U supermanager < backend/migrations/001_initial_schema.sql
```

---

## SSL/TLS Configuration

### Nginx with Let's Encrypt

```nginx
server {
    listen 80;
    server_name supermanager.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name supermanager.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Certbot Setup

```bash
# Install
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d supermanager.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Monitoring Setup

### Enable Monitoring Stack

```bash
docker compose --profile monitoring up -d
```

### Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### Configure Alerts

```yaml
# monitoring/alertmanager.yml
route:
  receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#alerts'
```

---

## Backup Configuration

### Automated Backups

```bash
# Create backup script
cat > /opt/backup-supermanager.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/supermanager"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump $DATABASE_URL | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Keep last 30 days
find $BACKUP_DIR -mtime +30 -delete
EOF

chmod +x /opt/backup-supermanager.sh

# Add to crontab
echo "0 2 * * * /opt/backup-supermanager.sh" | crontab -
```

### Restore from Backup

```bash
# Restore database
gunzip -c backup_20250115.sql.gz | psql $DATABASE_URL
```

---

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker compose logs backend

# Check container status
docker compose ps

# Inspect container
docker inspect supermanager-backend
```

#### Database Connection Failed

```bash
# Test connection
docker compose exec backend python -c "from database_supabase import get_supabase_client; print(get_supabase_client())"

# Check environment
docker compose exec backend env | grep SUPABASE
```

#### High Memory Usage

```bash
# Check memory
docker stats

# Limit memory in compose
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

#### API Response Slow

1. Check cache hit rate
2. Review database query performance
3. Scale horizontally if needed
4. Enable response compression

### Health Check Endpoints

```bash
# API health
curl https://your-api.com/api/health

# Detailed health
curl https://your-api.com/api/health/detailed

# Metrics
curl https://your-api.com/api/metrics
```

---

## Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] HTTPS enabled with valid certificate
- [ ] Rate limiting configured
- [ ] CORS origins restricted
- [ ] Database credentials are strong
- [ ] API keys are rotated regularly
- [ ] Logging enabled (no sensitive data)
- [ ] Backups tested and working
- [ ] Security headers configured
- [ ] Non-root Docker user

---

## Support

- **Issues**: Create a GitHub issue
- **Documentation**: See `/docs` directory
- **Logs**: Check Docker logs or cloud provider logs
