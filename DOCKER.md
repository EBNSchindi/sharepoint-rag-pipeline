# 🐳 Docker Guide - SharePoint RAG Pipeline

**Containerisierte Lösung mit Python 3.11 für maximale Kompatibilität**

## 🚀 Quick Start (Docker)

### 1. Prerequisites

```bash
# Docker und Docker Compose installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose (falls nicht enthalten)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Sofortige Verwendung

```bash
# In das Projektverzeichnis wechseln
cd sharepoint-rag-pipeline

# Container bauen und Pipeline testen
docker-compose up --build rag-pipeline

# Mit eigenen PDFs (Verzeichnis mounten)
docker-compose run --rm rag-pipeline python run_pipeline.py /app/input --force-all
```

### 3. Produktive Verwendung

```bash
# Environment-Datei erstellen
cp .env.example .env
nano .env  # INPUT_DIR anpassen

# Pipeline im Hintergrund starten
docker-compose up -d rag-pipeline

# Logs verfolgen
docker-compose logs -f rag-pipeline
```

---

## 📋 Verfügbare Services

### 🏭 Production Services

```bash
# Standard Pipeline (einmalige Ausführung)
docker-compose up rag-pipeline

# Scheduled Pipeline (automatische Ausführung via Cron)
docker-compose --profile scheduled up -d rag-scheduler

# External ChromaDB (separate Datenbank)
docker-compose --profile external-db up -d chromadb
```

### 🛠️ Development Services

```bash
# Development Environment (mit Jupyter)
docker-compose --profile dev up -d rag-dev

# In Development Container einsteigen
docker-compose exec rag-dev bash

# Jupyter Notebook starten
docker-compose exec rag-dev jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root
```

### 📊 Monitoring Services

```bash
# Log Viewer (Web Interface)
docker-compose --profile monitoring up -d log-viewer
# Zugriff: http://localhost:8080
```

---

## ⚙️ Konfiguration

### Environment Variables (.env)

```bash
# Erstelle .env Datei
cp .env.example .env
```

**Wichtigste Einstellungen:**

```env
# PDF Input Directory (Host-Pfad)
INPUT_DIR=/path/to/your/sharepoint/pdfs

# Pipeline Settings
MAX_WORKERS=4
MIN_QUALITY_SCORE=70

# Scheduled Run (Cron Format)
CRON_SCHEDULE=0 2 1 * *  # Monatlich um 2:00 Uhr

# Optional: OpenAI API
OPENAI_API_KEY=your-api-key
```

### Volume Mounts

```yaml
# Typische Volume-Konfiguration
volumes:
  - "/host/path/to/pdfs:/app/input:ro"      # Input (read-only)
  - "rag_data:/app/data"                    # Pipeline Data
  - "rag_logs:/app/logs"                    # Logs
  - "./config:/app/config:ro"               # Custom Config
```

---

## 🎯 Anwendungsfälle

### 1. Einmalige Verarbeitung

```bash
# Alle PDFs in einem Verzeichnis verarbeiten
docker run --rm \
  -v "/path/to/pdfs:/app/input:ro" \
  -v "$(pwd)/output:/app/data" \
  sharepoint-rag-pipeline:latest \
  python run_pipeline.py /app/input --force-all
```

### 2. Monatliche Automatisierung

```bash
# .env Datei konfigurieren
echo "INPUT_DIR=/data/sharepoint/pdfs" > .env
echo "CRON_SCHEDULE=0 2 1 * *" >> .env

# Scheduler starten
docker-compose --profile scheduled up -d rag-scheduler

# Status prüfen
docker-compose logs rag-scheduler
```

### 3. Development Setup

```bash
# Development Container starten
docker-compose --profile dev up -d rag-dev

# Code-Entwicklung
docker-compose exec rag-dev bash
cd /app
python test_pipeline.py
python run_pipeline.py sample_input --dry-run
```

### 4. Cluster-Deployment

```bash
# Production mit externer ChromaDB
docker-compose --profile external-db up -d chromadb
docker-compose up -d rag-pipeline

# Mit Monitoring
docker-compose --profile monitoring up -d log-viewer
```

---

## 🔧 Build Optionen

### Standard Build

```bash
# Production Image
docker build -t sharepoint-rag-pipeline:latest .

# Development Image
docker build --target development -t sharepoint-rag-pipeline:dev .
```

### Multi-Architecture Build

```bash
# Für AMD64 und ARM64
docker buildx build --platform linux/amd64,linux/arm64 \
  -t sharepoint-rag-pipeline:multi-arch \
  --push .
```

### Build Args

```bash
# Custom Python Version
docker build --build-arg PYTHON_VERSION=3.10 \
  -t sharepoint-rag-pipeline:py310 .

# With GPU Support
docker build --build-arg CUDA_VERSION=11.8 \
  -t sharepoint-rag-pipeline:gpu .
```

---

## 📊 Monitoring und Logs

### Log Access

```bash
# Container Logs
docker-compose logs -f rag-pipeline

# Pipeline Logs (in Container)
docker-compose exec rag-pipeline tail -f /app/logs/contextual_pipeline.log

# Web Log Viewer
docker-compose --profile monitoring up -d log-viewer
# Zugriff: http://localhost:8080/logs
```

### Health Checks

```bash
# Container Health prüfen
docker-compose ps

# Manual Health Check
docker-compose exec rag-pipeline python test_pipeline.py

# Pipeline Status
docker-compose exec rag-pipeline cat /app/data/reports/latest_report.json
```

### Performance Monitoring

```bash
# Resource Usage
docker stats rag-pipeline

# Container Metrics
docker-compose exec rag-pipeline sh -c "
  echo 'Memory Usage:'; free -h
  echo 'Disk Usage:'; df -h
  echo 'CPU Info:'; nproc
"
```

---

## 🔒 Security

### User Permissions

```bash
# Run with specific User ID
docker run --user 1000:1000 \
  -v "/path/to/pdfs:/app/input:ro" \
  sharepoint-rag-pipeline:latest
```

### Read-Only Mounts

```yaml
# Sicherheits-optimierte Mounts
volumes:
  - "/path/to/pdfs:/app/input:ro"           # Read-only Input
  - "/secure/path/config:/app/config:ro"    # Read-only Config
```

### Network Isolation

```yaml
# Custom Network
networks:
  rag-secure:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

---

## 🚀 Production Deployment

### Docker Swarm

```bash
# Swarm Mode aktivieren
docker swarm init

# Stack deployen
docker stack deploy -c docker-compose.yml rag-stack

# Services skalieren
docker service scale rag-stack_rag-pipeline=3
```

### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-pipeline
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-pipeline
  template:
    metadata:
      labels:
        app: rag-pipeline
    spec:
      containers:
      - name: rag-pipeline
        image: sharepoint-rag-pipeline:latest
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"
        volumeMounts:
        - name: input-volume
          mountPath: /app/input
          readOnly: true
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: input-volume
        hostPath:
          path: /data/sharepoint/pdfs
      - name: data-volume
        persistentVolumeClaim:
          claimName: rag-data-pvc
```

### CI/CD Integration

```yaml
# .github/workflows/docker.yml
name: Build and Deploy
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: |
        docker build -t ${{ secrets.REGISTRY }}/rag-pipeline:${{ github.sha }} .
        docker push ${{ secrets.REGISTRY }}/rag-pipeline:${{ github.sha }}
```

---

## 🔧 Troubleshooting

### Häufige Probleme

#### "Permission denied" Fehler

```bash
# User ID anpassen
docker run --user $(id -u):$(id -g) \
  -v "$(pwd):/app" \
  sharepoint-rag-pipeline:latest

# Oder Ownership korrigieren
sudo chown -R $(id -u):$(id -g) ./data
```

#### Out of Memory

```bash
# Memory Limit erhöhen
docker run --memory=8g \
  sharepoint-rag-pipeline:latest

# Oder in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 8G
```

#### Slow Performance

```bash
# CPU Limit erhöhen
docker run --cpus=4.0 \
  sharepoint-rag-pipeline:latest

# Oder weniger Worker
docker run -e MAX_WORKERS=2 \
  sharepoint-rag-pipeline:latest
```

#### Volume Mount Issues

```bash
# Absoluten Pfad verwenden
docker run -v "/absolute/path/to/pdfs:/app/input:ro" \
  sharepoint-rag-pipeline:latest

# SELinux Context (Red Hat/CentOS)
docker run -v "/path/to/pdfs:/app/input:ro,Z" \
  sharepoint-rag-pipeline:latest
```

### Debug Commands

```bash
# Container inspecten
docker-compose exec rag-pipeline bash

# Logs analysieren
docker-compose logs --tail=100 rag-pipeline

# Container Konfiguration prüfen
docker inspect rag-pipeline

# Environment Variables anzeigen
docker-compose exec rag-pipeline env | grep -E "(PIPELINE|MAX_|MIN_)"
```

---

## 📦 Image Variants

### Available Tags

```bash
# Latest stable
docker pull sharepoint-rag-pipeline:latest

# Development with tools
docker pull sharepoint-rag-pipeline:dev

# Specific version
docker pull sharepoint-rag-pipeline:v2.0.0

# GPU-enabled (wenn verfügbar)
docker pull sharepoint-rag-pipeline:gpu
```

### Custom Images

```bash
# Minimal image (ohne OCR)
docker build --target production-minimal \
  -t sharepoint-rag-pipeline:minimal .

# With additional languages
docker build --build-arg LANGUAGES="de,fr,es" \
  -t sharepoint-rag-pipeline:multilang .
```

---

## 🎮 Beispiel-Workflows

### Backup und Restore

```bash
# Data Backup
docker run --rm \
  -v rag_data:/source \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/rag-data-$(date +%Y%m%d).tar.gz -C /source .

# Data Restore  
docker run --rm \
  -v rag_data:/target \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/rag-data-20231201.tar.gz -C /target
```

### Batch Processing

```bash
# Mehrere Verzeichnisse verarbeiten
for dir in /data/sharepoint/*/; do
  echo "Processing $dir..."
  docker run --rm \
    -v "$dir:/app/input:ro" \
    -v "rag_data:/app/data" \
    sharepoint-rag-pipeline:latest \
    python run_pipeline.py /app/input
done
```

### Integration Testing

```bash
# Test mit Sample-Daten
docker run --rm \
  -v "$(pwd)/test_data:/app/input:ro" \
  sharepoint-rag-pipeline:latest \
  python run_pipeline.py /app/input --dry-run

# Vollständiger Integration Test
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## 🔄 Maintenance

### Updates

```bash
# Image aktualisieren
docker-compose pull rag-pipeline
docker-compose up -d rag-pipeline

# Data Migration (falls nötig)
docker-compose exec rag-pipeline python migrate_data.py
```

### Cleanup

```bash
# Ungenutzte Images entfernen
docker image prune -f

# Alle RAG-bezogenen Ressourcen entfernen
docker-compose down -v
docker rmi sharepoint-rag-pipeline:latest
```

**Die Docker-Integration ist vollständig und production-ready!** 🎉

**Nächste Schritte:**
1. `.env` Datei konfigurieren
2. `docker-compose up --build rag-pipeline` 
3. PDF-Verzeichnis mounten und verarbeiten lassen
4. Für Produktion: Scheduled Service nutzen