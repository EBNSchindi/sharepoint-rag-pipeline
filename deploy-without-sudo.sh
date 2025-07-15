#!/bin/bash

# Docker Deployment ohne sudo-Berechtigung
# Dieser Skript umgeht Docker-Berechtigungsprobleme

echo "🚀 Docker Deployment ohne sudo"
echo "================================"

# Prüfe aktuelle Benutzer-ID
USER_ID=$(id -u)
GROUP_ID=$(id -g)
echo "Current user: $USER (ID: $USER_ID:$GROUP_ID)"

# Erstelle docker-compose wrapper falls nicht vorhanden
if ! command -v docker-compose &> /dev/null; then
    echo "📝 Erstelle docker-compose wrapper..."
    cat > ./docker-compose-wrapper << 'EOF'
#!/bin/bash
docker compose "$@"
EOF
    chmod +x ./docker-compose-wrapper
    echo "✅ docker-compose wrapper erstellt"
fi

# Bereite Verzeichnisse vor
echo "📁 Bereite Verzeichnisse vor..."
mkdir -p data/{input,processed,state,vectors,reports,backups}
mkdir -p logs
chmod -R 755 data logs sample_input 2>/dev/null || true

# Erstelle temporäre docker-compose.yml mit angepassten Berechtigungen
echo "⚙️  Erstelle angepasste docker-compose.yml..."
cat > docker-compose-temp.yml << EOF
services:
  rag-pipeline:
    build:
      context: .
      target: production
      args:
        USER_ID: $USER_ID
        GROUP_ID: $GROUP_ID
    image: sharepoint-rag-pipeline:latest
    container_name: rag-pipeline
    restart: "no"
    user: "$USER_ID:$GROUP_ID"
    volumes:
      - "./sample_input:/app/input:ro"
      - "./data:/app/data"
      - "./logs:/app/logs"
      - "./config:/app/config:ro"
    environment:
      - PIPELINE_MODE=production
      - LOG_LEVEL=INFO
      - MAX_WORKERS=2
      - MIN_QUALITY_SCORE=70
    command: >
      sh -c "
        echo 'Starting RAG Pipeline...' &&
        python test_pipeline.py &&
        python run_pipeline.py /app/input --workers 2 --verbose
      "
    working_dir: /app

volumes:
  rag_data:
    driver: local
  rag_logs:
    driver: local
EOF

# Prüfe Docker-Zugriff
echo "🔍 Prüfe Docker-Zugriff..."
if docker info > /dev/null 2>&1; then
    echo "✅ Docker ist zugänglich"
    
    # Stoppe existierende Container
    echo "🛑 Stoppe existierende Container..."
    docker stop rag-pipeline 2>/dev/null || true
    docker rm rag-pipeline 2>/dev/null || true
    
    # Baue Image mit korrekten Berechtigungen
    echo "🏗️  Baue Docker Image..."
    docker build \
        --build-arg USER_ID=$USER_ID \
        --build-arg GROUP_ID=$GROUP_ID \
        -t sharepoint-rag-pipeline:latest \
        --target production \
        . || {
        echo "❌ Build fehlgeschlagen"
        exit 1
    }
    
    echo "✅ Docker Image erfolgreich gebaut"
    
    # Starte Container
    echo "🚀 Starte Container..."
    docker compose -f docker-compose-temp.yml up --build rag-pipeline
    
elif command -v docker &> /dev/null; then
    echo "❌ Docker ist installiert, aber nicht zugänglich"
    echo ""
    echo "Lösungen:"
    echo "1. Neuanmeldung nach Docker-Gruppe-Zuordnung"
    echo "2. Oder: newgrp docker"
    echo "3. Oder: sudo ./deploy-without-sudo.sh"
    echo ""
    echo "Manuelle Befehle:"
    echo "sudo usermod -aG docker $USER"
    echo "sudo systemctl start docker"
    echo "newgrp docker"
else
    echo "❌ Docker ist nicht installiert"
    echo "Installiere Docker: https://docs.docker.com/engine/install/"
fi

# Cleanup
echo "🧹 Cleanup..."
rm -f docker-compose-temp.yml ./docker-compose-wrapper

echo "✅ Deployment-Skript abgeschlossen"