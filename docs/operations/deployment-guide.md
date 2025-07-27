# Deployment Guide

Complete guide for deploying Apollonia in various environments, from development to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Configuration Management](#configuration-management)
- [Security Considerations](#security-considerations)
- [Backup and Recovery](#backup-and-recovery)
- [Monitoring Setup](#monitoring-setup)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, RHEL 8+) or macOS
- **Docker**: Version 20.10+ with Docker Compose v2.0+
- **CPU**: Minimum 4 cores, recommended 8+ cores
- **RAM**: Minimum 8GB, recommended 16GB+ (32GB for ML features)
- **Storage**: 50GB+ for application and databases
- **Network**: Stable internet connection for package downloads

### Software Dependencies

```bash
# Install Docker
curl -fsSL https://get.docker.com | bash

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## Development Deployment

### Quick Start

1. **Clone the repository**:

   ```bash
   git clone https://github.com/SimplicityGuy/apollonia.git
   cd apollonia
   ```

1. **Create environment file**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

1. **Start all services**:

   ```bash
   docker-compose up -d
   ```

1. **Verify services are running**:

   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

1. **Access the application**:

   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - RabbitMQ Management: http://localhost:15672
   - Neo4j Browser: http://localhost:7474

### Development Configuration

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  api:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./api:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Update all secrets and passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up backup procedures
- [ ] Configure monitoring and alerting
- [ ] Review security settings
- [ ] Test deployment in staging environment

### Production Configuration

1. **Create production environment file**:

   ```bash
   # .env.production
   NODE_ENV=production

   # Database Configuration
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   POSTGRES_DB=apollonia
   POSTGRES_USER=apollonia_user
   POSTGRES_PASSWORD=<strong-password>

   # Neo4j Configuration
   NEO4J_URI=bolt://neo4j:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=<strong-password>

   # RabbitMQ Configuration
   RABBITMQ_DEFAULT_USER=apollonia
   RABBITMQ_DEFAULT_PASS=<strong-password>
   AMQP_CONNECTION_STRING=amqp://apollonia:<password>@rabbitmq:5672/

   # Redis Configuration
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=<strong-password>

   # API Configuration
   SECRET_KEY=<generate-with-openssl-rand-hex-32>
   JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # ML Configuration
   ML_MODEL_PATH=/models
   ENABLE_GPU=false
   ```

1. **Create production Docker Compose file**:

   ```yaml
   # docker-compose.prod.yml
   version: '3.8'

   services:
     postgres:
       restart: always
       volumes:
         - postgres_data:/var/lib/postgresql/data
       environment:
         - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
       secrets:
         - postgres_password

     api:
       restart: always
       environment:
         - NODE_ENV=production
       deploy:
         replicas: 2
         resources:
           limits:
             cpus: '2'
             memory: 4G

   volumes:
     postgres_data:
       driver: local

   secrets:
     postgres_password:
       file: ./secrets/postgres_password.txt
   ```

1. **Deploy with Docker Swarm**:

   ```bash
   # Initialize swarm
   docker swarm init

   # Deploy stack
   docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml apollonia

   # Check services
   docker service ls
   docker service logs apollonia_api
   ```

### SSL/TLS Configuration

1. **Using Let's Encrypt with Traefik**:
   ```yaml
   # traefik.yml
   services:
     traefik:
       image: traefik:v2.9
       command:
         - "--providers.docker=true"
         - "--entrypoints.web.address=:80"
         - "--entrypoints.websecure.address=:443"
         - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
         - "--certificatesresolvers.letsencrypt.acme.storage=/certificates/acme.json"
         - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock:ro
         - traefik_certificates:/certificates

     api:
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.api.rule=Host(`api.apollonia.example.com`)"
         - "traefik.http.routers.api.entrypoints=websecure"
         - "traefik.http.routers.api.tls.certresolver=letsencrypt"
   ```

## Kubernetes Deployment

### Helm Chart Installation

```bash
# Add Apollonia Helm repository
helm repo add apollonia https://charts.apollonia.io
helm repo update

# Install with custom values
helm install apollonia apollonia/apollonia \
  --namespace apollonia \
  --create-namespace \
  -f values.yaml
```

### Sample Kubernetes Configuration

```yaml
# values.yaml
global:
  storageClass: fast-ssd

postgresql:
  enabled: true
  auth:
    postgresPassword: <secure-password>
  persistence:
    size: 50Gi

neo4j:
  enabled: true
  auth:
    password: <secure-password>
  core:
    persistentVolume:
      size: 100Gi

rabbitmq:
  enabled: true
  auth:
    username: apollonia
    password: <secure-password>

api:
  replicaCount: 3
  image:
    repository: ghcr.io/simplicityguy/apollonia-api
    tag: latest
  ingress:
    enabled: true
    className: nginx
    hosts:
      - host: api.apollonia.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: apollonia-api-tls
        hosts:
          - api.apollonia.example.com

frontend:
  replicaCount: 2
  image:
    repository: ghcr.io/simplicityguy/apollonia-frontend
    tag: latest
  ingress:
    enabled: true
    className: nginx
    hosts:
      - host: apollonia.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: apollonia-frontend-tls
        hosts:
          - apollonia.example.com
```

### Kubernetes Resources

```yaml
# apollonia-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: apollonia

---
# apollonia-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: apollonia-secrets
  namespace: apollonia
type: Opaque
stringData:
  postgres-password: <base64-encoded-password>
  neo4j-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-secret>

---
# apollonia-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apollonia-config
  namespace: apollonia
data:
  NODE_ENV: "production"
  API_PORT: "8000"
  LOG_LEVEL: "info"
```

## Cloud Deployments

### AWS Deployment

1. **Using ECS with Fargate**:

   ```bash
   # Create task definition
   aws ecs register-task-definition \
     --family apollonia \
     --cli-input-json file://task-definition.json

   # Create service
   aws ecs create-service \
     --cluster apollonia-cluster \
     --service-name apollonia-api \
     --task-definition apollonia:1 \
     --desired-count 2 \
     --launch-type FARGATE
   ```

1. **Using EKS**:

   ```bash
   # Create EKS cluster
   eksctl create cluster \
     --name apollonia \
     --region us-west-2 \
     --nodegroup-name standard-workers \
     --node-type t3.large \
     --nodes 3

   # Deploy using Helm
   helm install apollonia ./charts/apollonia
   ```

### Google Cloud Platform

```bash
# Create GKE cluster
gcloud container clusters create apollonia \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2

# Get credentials
gcloud container clusters get-credentials apollonia \
  --zone us-central1-a

# Deploy
kubectl apply -f kubernetes/
```

### Azure Deployment

```bash
# Create AKS cluster
az aks create \
  --resource-group apollonia-rg \
  --name apollonia-cluster \
  --node-count 3 \
  --node-vm-size Standard_DS2_v2

# Get credentials
az aks get-credentials \
  --resource-group apollonia-rg \
  --name apollonia-cluster

# Deploy
helm install apollonia ./charts/apollonia
```

## Configuration Management

### Environment Variables

| Variable            | Description          | Default           | Required |
| ------------------- | -------------------- | ----------------- | -------- |
| `NODE_ENV`          | Environment mode     | development       | Yes      |
| `API_PORT`          | API service port     | 8000              | No       |
| `POSTGRES_HOST`     | PostgreSQL host      | postgres          | Yes      |
| `POSTGRES_PORT`     | PostgreSQL port      | 5432              | No       |
| `POSTGRES_DB`       | Database name        | apollonia         | Yes      |
| `POSTGRES_USER`     | Database user        | apollonia         | Yes      |
| `POSTGRES_PASSWORD` | Database password    | -                 | Yes      |
| `NEO4J_URI`         | Neo4j connection URI | bolt://neo4j:7687 | Yes      |
| `NEO4J_USER`        | Neo4j username       | neo4j             | Yes      |
| `NEO4J_PASSWORD`    | Neo4j password       | -                 | Yes      |
| `RABBITMQ_HOST`     | RabbitMQ host        | rabbitmq          | Yes      |
| `RABBITMQ_PORT`     | RabbitMQ port        | 5672              | No       |
| `REDIS_HOST`        | Redis host           | redis             | Yes      |
| `REDIS_PORT`        | Redis port           | 6379              | No       |
| `JWT_SECRET_KEY`    | JWT signing key      | -                 | Yes      |
| `ML_MODELS_PATH`    | ML models directory  | /models           | No       |
| `ENABLE_GPU`        | Enable GPU for ML    | false             | No       |

### Configuration Files

```yaml
# config/production.yml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  pool_size: 20
  max_overflow: 40
  pool_timeout: 30

cache:
  ttl: 3600
  max_size: 1000

ml:
  batch_size: 32
  model_cache_size: 5
  preprocessing_workers: 2
```

## Security Considerations

### Network Security

1. **Firewall Rules**:

   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp    # HTTP
   ufw allow 443/tcp   # HTTPS
   ufw allow 22/tcp    # SSH (restrict source IPs)
   ufw enable
   ```

1. **Docker Network Isolation**:

   ```yaml
   networks:
     frontend:
       driver: bridge
     backend:
       driver: bridge
       internal: true
     data:
       driver: bridge
       internal: true
   ```

### Secrets Management

1. **Using Docker Secrets**:

   ```bash
   # Create secrets
   echo "strong-password" | docker secret create postgres_password -
   echo "jwt-secret-key" | docker secret create jwt_secret -
   ```

1. **Using Kubernetes Secrets**:

   ```bash
   # Create from files
   kubectl create secret generic apollonia-secrets \
     --from-file=postgres-password=./postgres-password.txt \
     --from-file=jwt-secret=./jwt-secret.txt
   ```

1. **Using AWS Secrets Manager**:

   ```bash
   # Create secret
   aws secretsmanager create-secret \
     --name apollonia/production/database \
     --secret-string '{"password":"strong-password"}'
   ```

### Security Hardening

1. **Run as non-root user**:

   ```dockerfile
   USER 1001:1001
   ```

1. **Read-only root filesystem**:

   ```yaml
   securityContext:
     readOnlyRootFilesystem: true
     runAsNonRoot: true
     runAsUser: 1001
   ```

1. **Network policies**:

   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: api-network-policy
   spec:
     podSelector:
       matchLabels:
         app: api
     policyTypes:
     - Ingress
     - Egress
     ingress:
     - from:
       - podSelector:
           matchLabels:
             app: frontend
       ports:
       - protocol: TCP
         port: 8000
   ```

## Backup and Recovery

### Database Backups

1. **PostgreSQL Backup**:

   ```bash
   # Backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/backups/postgres"

   docker exec postgres pg_dump \
     -U apollonia \
     -d apollonia \
     -f /tmp/apollonia_${DATE}.sql

   docker cp postgres:/tmp/apollonia_${DATE}.sql ${BACKUP_DIR}/

   # Compress and encrypt
   gzip ${BACKUP_DIR}/apollonia_${DATE}.sql
   gpg --encrypt --recipient backup@example.com \
     ${BACKUP_DIR}/apollonia_${DATE}.sql.gz
   ```

1. **Neo4j Backup**:

   ```bash
   # Online backup
   docker exec neo4j neo4j-admin backup \
     --database=neo4j \
     --backup-dir=/backups \
     --name=apollonia-backup-${DATE}
   ```

1. **Automated Backups with CronJob**:

   ```yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: backup-databases
   spec:
     schedule: "0 2 * * *"  # Daily at 2 AM
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: backup
               image: apollonia/backup:latest
               command: ["/scripts/backup.sh"]
               volumeMounts:
               - name: backup-storage
                 mountPath: /backups
   ```

### Disaster Recovery

1. **Recovery Time Objective (RTO)**: < 1 hour
1. **Recovery Point Objective (RPO)**: < 24 hours

```bash
# Restore PostgreSQL
docker exec -i postgres psql -U apollonia < backup.sql

# Restore Neo4j
docker exec neo4j neo4j-admin restore \
  --from=/backups/apollonia-backup-20240101 \
  --database=neo4j \
  --force
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'apollonia-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'rabbitmq'
    static_configs:
      - targets: ['rabbitmq:15692']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards

Import provided dashboards:

- `dashboards/apollonia-overview.json`
- `dashboards/service-health.json`
- `dashboards/database-performance.json`

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: apollonia
    rules:
      - alert: ServiceDown
        expr: up{job=~"apollonia-.*"} == 0
        for: 5m
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes > 0.9 * container_spec_memory_limit_bytes
        for: 5m
        annotations:
          summary: "High memory usage in {{ $labels.container_name }}"

      - alert: DatabaseConnectionFailure
        expr: pg_up == 0
        for: 1m
        annotations:
          summary: "PostgreSQL database is unreachable"
```

## Maintenance

### Rolling Updates

```bash
# Docker Swarm
docker service update --image apollonia/api:v2.0 apollonia_api

# Kubernetes
kubectl set image deployment/api api=apollonia/api:v2.0

# Zero-downtime deployment
kubectl rollout status deployment/api
kubectl rollout history deployment/api
```

### Health Checks

```yaml
# Docker health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# Kubernetes probes
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Troubleshooting

### Common Issues

1. **Service won't start**:

   ```bash
   # Check logs
   docker-compose logs -f service_name

   # Check resources
   docker system df
   docker system prune -a
   ```

1. **Database connection errors**:

   ```bash
   # Test connection
   docker exec -it postgres psql -U apollonia -d apollonia

   # Check network
   docker network ls
   docker network inspect apollonia_backend
   ```

1. **Performance issues**:

   ```bash
   # Check resource usage
   docker stats

   # Profile application
   docker exec api python -m cProfile -o profile.stats main.py
   ```

### Support

For deployment support:

- Documentation: https://docs.apollonia.io
- Issues: https://github.com/SimplicityGuy/apollonia/issues
- Community: https://discord.gg/apollonia
