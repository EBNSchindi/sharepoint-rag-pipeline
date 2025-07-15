# 🚀 SharePoint RAG Pipeline - Docker Quick Start Guide

**Von 0 auf 100 in 5 Minuten!** 🚀💨

Diese Anleitung funktioniert auf **Windows**, **macOS** und **Linux** mit Docker.

## 📋 Voraussetzungen

### Docker Installation prüfen/installieren

<details>
<summary><b>🪟 Windows</b></summary>

1. **Docker Desktop installieren:**
   ```powershell
   # Lade Docker Desktop herunter: https://www.docker.com/products/docker-desktop
   # Oder mit winget:
   winget install Docker.DockerDesktop
   ```

2. **Installation verifizieren:**
   ```powershell
   docker --version
   docker compose version
   ```

3. **WSL2 Backend aktivieren** (empfohlen):
   - Docker Desktop → Settings → General → "Use WSL 2 based engine"

</details>

<details>
<summary><b>🐧 Linux (Ubuntu/Debian)</b></summary>

1. **Docker installieren:**
   ```bash
   # Docker Engine installieren
   curl -fsSL https://get.docker.com | sh
   
   # Benutzer zur Docker-Gruppe hinzufügen
   sudo usermod -aG docker $USER
   
   # Neu einloggen oder newgrp verwenden
   newgrp docker
   ```

2. **Docker Compose installieren:**
   ```bash
   # Moderne Docker-Installation hat bereits compose als Plugin
   docker compose version
   ```

3. **Installation verifizieren:**
   ```bash
   docker --version
   docker compose version
   ```

</details>

<details>
<summary><b>🍎 macOS</b></summary>

1. **Docker Desktop installieren:**
   ```bash
   # Mit Homebrew:
   brew install --cask docker
   
   # Oder direkt herunterladen: https://www.docker.com/products/docker-desktop
   ```

2. **Installation verifizieren:**
   ```bash
   docker --version
   docker compose version
   ```

</details>

---

## ⚡ 3-Schritt Quick Start

### 1️⃣ Repository vorbereiten

```bash
# Repository klonen/extrahieren (falls noch nicht geschehen)
cd sharepoint-rag-pipeline

# Environment-Datei erstellen
cp .env.example .env
```

### 2️⃣ Input-Verzeichnis konfigurieren

Öffne die `.env` Datei und passe den `INPUT_DIR` an:

<details>
<summary><b>🪟 Windows Beispiele</b></summary>

```env
# Absolute Windows-Pfade (empfohlen):
INPUT_DIR=C:\Users\YourName\Documents\PDFs

# Oder relative Pfade:
INPUT_DIR=.\input

# UNC-Pfade (Netzwerk):
INPUT_DIR=\\server\share\documents
```

</details>

<details>
<summary><b>🐧 Linux Beispiele</b></summary>

```env
# Absolute Linux-Pfade:
INPUT_DIR=/home/username/Documents/pdfs
INPUT_DIR=/var/data/sharepoint/documents

# Relative Pfade:
INPUT_DIR=./input
```

</details>

<details>
<summary><b>🍎 macOS Beispiele</b></summary>

```env
# Absolute macOS-Pfade:
INPUT_DIR=/Users/username/Documents/PDFs
INPUT_DIR=/Volumes/SharePoint/Documents

# Relative Pfade:
INPUT_DIR=./input
```

</details>

### 3️⃣ Pipeline ausführen

```bash
# Schneller Start (nur PDF-Verarbeitung, 5-10 min):
make build-minimal
make process INPUT=/path/to/your/pdfs

# Vollständiger Build (alle Features, 15-30 min):
make build
make process INPUT=/path/to/your/pdfs

# Oder mit docker compose direkt:
docker compose up --build rag-pipeline
```

**Das war's!** 🎉 Die Pipeline läuft und verarbeitet Ihre Dokumente.

**💡 Tipp:** Verwenden Sie `make build-minimal` für den ersten Test - das ist viel schneller!

---

## 🔧 Detaillierte Konfiguration

### Environment-Variablen anpassen

Bearbeite die `.env` Datei für erweiterte Konfiguration:

```env
# Anzahl paralleler Worker (anpassen je nach CPU/RAM)
MAX_WORKERS=4

# Qualitätsschwelle für Chunks (0-100)
MIN_QUALITY_SCORE=70

# Log-Level
LOG_LEVEL=INFO

# Optional: OpenAI API für erweiterte Features
OPENAI_API_KEY=your-api-key-here
```

### Verschiedene Ausführungsmodi

<details>
<summary><b>🔨 Entwicklung</b></summary>

```bash
# Development-Container starten
make setup-dev
make run-dev

# Interaktive Shell
make shell-dev

# Jupyter Notebook starten
make jupyter
# Dann: http://localhost:8888
```

</details>

<details>
<summary><b>🏭 Produktion</b></summary>

```bash
# Production-Pipeline
make build
make process INPUT=/path/to/pdfs

# Mit eigenen Ressourcen-Limits
docker compose up --build \
  --scale rag-pipeline=1 \
  rag-pipeline
```

</details>

<details>
<summary><b>⏰ Geplante Ausführung</b></summary>

```bash
# Monatliche Automatisierung einrichten
echo "CRON_SCHEDULE=0 2 1 * *" >> .env
make run-scheduled

# Status prüfen
make status
make logs-scheduler
```

</details>

<details>
<summary><b>📊 Monitoring</b></summary>

```bash
# Monitoring-Dashboard starten
make monitor
# Dashboard: http://localhost:8080

# Container-Status anzeigen
make status

# Live-Logs verfolgen
make logs
```

</details>

---

## 🎯 Beispiel-Workflows

### Einmalige Verarbeitung
```bash
# Test-Lauf (zeigt nur, was verarbeitet würde)
make process-dry INPUT=/path/to/pdfs

# Echte Verarbeitung
make process INPUT=/path/to/pdfs

# Mit erweiterten Optionen
docker compose run --rm rag-pipeline \
  python run_pipeline.py /app/input \
  --workers 8 \
  --force-all \
  --min-quality 80
```

### Batch-Verarbeitung
```bash
# Mehrere Verzeichnisse verarbeiten
for dir in /path/to/docs/*; do
  make process INPUT="$dir"
done
```

### Monitoring und Logs
```bash
# Verarbeitungsberichte ansehen
docker compose exec rag-pipeline \
  cat /app/data/reports/latest_report.json

# Live-Performance-Monitoring
make stats

# Gesundheitsprüfung
make health
```

---

## 🛠️ Erweiterte Docker-Befehle

### Container-Management
```bash
# Alle Dienste starten
docker compose up -d

# Bestimmten Dienst neu starten
docker compose restart rag-pipeline

# Logs eines bestimmten Dienstes
docker compose logs -f rag-pipeline

# In laufenden Container einsteigen
docker compose exec rag-pipeline bash
```

### Daten-Management
```bash
# Backup erstellen
make backup

# Daten-Volumes anzeigen
docker volume ls | grep rag

# Volume-Größe prüfen
docker system df -v
```

### Bereinigung
```bash
# Container stoppen und entfernen
make clean

# Container + Volumes entfernen
make clean-all

# Images entfernen
make clean-images

# Vollständige Bereinigung
docker system prune -a --volumes
```

---

## 🔍 Fehlerbehebung

### Häufige Probleme und Lösungen

<details>
<summary><b>❌ "Permission denied" auf Linux</b></summary>

```bash
# Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neu einloggen oder:
newgrp docker

# Testen
docker run hello-world
```

</details>

<details>
<summary><b>❌ "Volume mount failed" auf Windows</b></summary>

1. **Docker Desktop File Sharing aktivieren:**
   - Docker Desktop → Settings → Resources → File Sharing
   - Laufwerk C:\ (oder entsprechendes) hinzufügen

2. **Pfad-Format prüfen:**
   ```env
   # Richtig:
   INPUT_DIR=C:\Users\Name\Documents\PDFs
   
   # Falsch:
   INPUT_DIR=C:/Users/Name/Documents/PDFs (in .env)
   ```

</details>

<details>
<summary><b>❌ "No space left on device"</b></summary>

```bash
# Docker-Speicher bereinigen
docker system prune -a --volumes

# Docker Root-Verzeichnis verschieben (Linux):
sudo systemctl stop docker
sudo mv /var/lib/docker /new/location/docker
sudo ln -s /new/location/docker /var/lib/docker
sudo systemctl start docker
```

</details>

<details>
<summary><b>❌ Pipeline läuft nicht / Container startet nicht</b></summary>

```bash
# Detaillierte Logs anzeigen
docker compose logs rag-pipeline

# Container-Status prüfen
docker compose ps

# Gesundheitsprüfung
docker compose exec rag-pipeline python test_pipeline.py

# Dependencies überprüfen
docker compose exec rag-pipeline pip list
```

</details>

<details>
<summary><b>❌ Langsame Performance</b></summary>

1. **Ressourcen erhöhen:**
   ```env
   # In .env:
   MAX_WORKERS=2  # Reduzieren bei wenig RAM
   ```

2. **Docker-Ressourcen anpassen:**
   - Docker Desktop → Settings → Resources
   - CPU: 4+ Kerne, RAM: 8+ GB

3. **Volume-Performance (Windows):**
   ```yaml
   # In docker-compose.yml für bessere Performance:
   volumes:
     - type: bind
       source: C:\path\to\data
       target: /app/input
       consistency: cached
   ```

</details>

---

## 📈 Performance-Optimierung

### Hardware-Empfehlungen
- **CPU:** 4+ Kerne
- **RAM:** 8+ GB (16+ GB für große Dokumente)
- **Storage:** SSD empfohlen

### Docker-Optimierung

<details>
<summary><b>🪟 Windows-spezifisch</b></summary>

```bash
# WSL2 Memory-Limit setzen
# %USERPROFILE%\.wslconfig erstellen:
[wsl2]
memory=8GB
processors=4
```

</details>

<details>
<summary><b>🐧 Linux-spezifisch</b></summary>

```bash
# Docker Daemon-Konfiguration
# /etc/docker/daemon.json:
{
  "storage-driver": "overlay2",
  "log-driver": "local",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

</details>

### Pipeline-Optimierung
```env
# In .env für bessere Performance:
MAX_WORKERS=4              # Je nach CPU-Kerne
MIN_QUALITY_SCORE=70       # Niedrigerer Wert = mehr Chunks
TIMEOUT_PER_DOCUMENT=300   # Timeout erhöhen für große PDFs
LOG_LEVEL=WARNING          # Weniger Logs für bessere Performance
```

---

## 🔧 Makefile-Referenz

Alle verfügbaren Befehle:

```bash
# Build-Befehle
make help              # Zeigt alle verfügbaren Befehle
make build             # Baut das Production-Image (vollständig)
make build-minimal     # Baut minimale Version (nur PDF-Verarbeitung)
make build-no-ai       # Baut ohne AI/ML-Dependencies
make setup             # Komplette Einrichtung

# Ausführung
make process INPUT=... # Verarbeitet Dokumente
make run-dev           # Startet Development-Umgebung
make monitor           # Startet Monitoring-Dashboard

# Wartung
make logs              # Zeigt Live-Logs
make clean             # Bereinigt Container
make backup            # Erstellt Daten-Backup
make health            # Gesundheitsprüfung

# Plattform-spezifische Hilfe
make setup-linux       # Linux-Setup-Anweisungen
make setup-windows     # Windows-Setup-Anweisungen
make setup-macos       # macOS-Setup-Anweisungen
```

---

## 🆘 Support

### Log-Dateien finden
```bash
# Container-Logs
docker compose logs rag-pipeline > pipeline.log

# Application-Logs (im Container)
docker compose exec rag-pipeline ls -la /app/logs/

# Volume-Logs (auf Host)
docker volume inspect rag_logs
```

### Debug-Modus aktivieren
```env
# In .env:
LOG_LEVEL=DEBUG
DEBUG_AGENTS=true
DEVELOPMENT_MODE=true
```

### Community & Issues
- **GitHub Issues:** [sharepoint-rag-pipeline/issues](https://github.com/your-repo/sharepoint-rag-pipeline/issues)
- **Diskussionen:** [sharepoint-rag-pipeline/discussions](https://github.com/your-repo/sharepoint-rag-pipeline/discussions)

---

## 📚 Weiterführende Dokumentation

- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technische Architektur
- 🔧 **[CONFIGURATION.md](CONFIGURATION.md)** - Detaillierte Konfiguration
- 🐳 **[DOCKER.md](DOCKER.md)** - Docker-spezifische Details
- 🚨 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Erweiterte Fehlerbehebung
- 📖 **[EXAMPLES.md](EXAMPLES.md)** - Beispiele und Use Cases

---

🎉 **Viel Erfolg mit Ihrer SharePoint RAG Pipeline!**