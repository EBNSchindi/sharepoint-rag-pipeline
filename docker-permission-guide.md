# Docker Permission Guide

## Problem
Docker-Berechtigungsprobleme beim Deployment der RAG Pipeline.

## Lösung

### 1. Docker-Berechtigung einrichten (einmalig)

```bash
# Docker-Gruppe hinzufügen (benötigt sudo)
sudo usermod -aG docker $USER

# Docker-Service starten
sudo systemctl start docker

# Neuanmeldung erforderlich
# Oder: newgrp docker
```

### 2. Docker-Compose installieren (falls nicht vorhanden)

```bash
# Docker Compose Plugin (moderne Variante)
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Oder: docker-compose Wrapper verwenden
echo '#!/bin/bash' > docker-compose
echo 'docker compose "$@"' >> docker-compose
chmod +x docker-compose
```

### 3. Deployment-Skript verwenden

```bash
# Skript ausführbar machen
chmod +x docker-deploy.sh

# Deployment starten
./docker-deploy.sh
```

### 4. Manuelle Deployment-Optionen

#### Option A: Docker Run (einfach)
```bash
# Image bauen
docker build -t sharepoint-rag-pipeline:latest .

# Container starten
docker run --rm \
  --user $(id -u):$(id -g) \
  -v "$(pwd)/sample_input:/app/input:ro" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  sharepoint-rag-pipeline:latest \
  python run_pipeline.py /app/input --workers 2
```

#### Option B: Docker Compose (empfohlen)
```bash
# Mit docker compose plugin
docker compose build --no-cache
docker compose up rag-pipeline

# Oder mit docker-compose (legacy)
docker-compose build --no-cache
docker-compose up rag-pipeline
```

### 5. Debugging

```bash
# Container-Logs anzeigen
docker logs rag-pipeline

# Container inspizieren
docker exec -it rag-pipeline bash

# Volumes prüfen
docker volume ls
docker volume inspect sharepoint-rag-pipeline_rag_data
```

### 6. Troubleshooting

| Problem | Lösung |
|---------|--------|
| `permission denied` | `sudo usermod -aG docker $USER` + logout/login |
| `docker-compose not found` | `docker compose` verwenden oder wrapper installieren |
| `No such file or directory` | `docker-deploy.sh` verwenden |
| `Build failed` | `docker build --no-cache` |
| `Volume mount failed` | Pfade in `.env` prüfen |

### 7. Produktions-Setup

```bash
# Systemd Service erstellen
sudo tee /etc/systemd/system/rag-pipeline.service << EOF
[Unit]
Description=SharePoint RAG Pipeline
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/sharepoint-rag-pipeline
ExecStart=/usr/bin/docker compose up -d rag-pipeline
ExecStop=/usr/bin/docker compose down
User=appuser
Group=docker

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl enable rag-pipeline
sudo systemctl start rag-pipeline
```

## Ergebnis

Nach erfolgreicher Einrichtung können Sie die Pipeline mit einem einzigen Befehl starten:

```bash
./docker-deploy.sh
```

Die Pipeline verarbeitet automatisch alle PDFs im `sample_input` Verzeichnis und speichert die Ergebnisse in `data/`.