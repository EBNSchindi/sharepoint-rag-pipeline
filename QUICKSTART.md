# 🚀 SharePoint RAG Pipeline - Quick Start Guide

**Von 0 auf 100 in 3 Minuten!** 🚀💨

## ⚡ Der schnellste Weg (3 Befehle)

```bash
# 1. Projekt vorbereiten
cd sharepoint-rag-pipeline
cp .env.example .env

# 2. Setup ausführen
make setup

# 3. PDFs verarbeiten
make process INPUT=/path/to/your/pdfs
```

**Das war's!** 🎉 Die Pipeline läuft und verarbeitet Ihre Dokumente.

**✅ Erfolgreich getestet:** Business Intelligence PDF (10 Seiten, 25.389 Zeichen → 4 kontextuelle Chunks)

---

## 🐳 Docker Quick Start (Empfohlen)

### Voraussetzungen prüfen
```bash
# Docker verfügbar?
docker --version          # Sollte 20.10+ sein
docker-compose --version  # Sollte 1.29+ sein

# Falls nicht installiert:
curl -fsSL https://get.docker.com | sh
```

### 1️⃣ Basis-Setup (einmalig)
```bash
cd sharepoint-rag-pipeline

# Environment konfigurieren
cp .env.example .env
nano .env  # INPUT_DIR auf Ihr PDF-Verzeichnis setzen

# Container bauen
make setup
```

### 2️⃣ Pipeline ausführen
```bash
# Option A: Mit Makefile (am einfachsten)
make process INPUT=/absolute/path/to/pdfs

# Option B: Mit docker-compose (nutzt .env)
docker-compose up rag-pipeline

# Option C: Mit docker run (explizite Pfade)
docker run --rm \
  -v "/absolute/path/to/pdfs:/app/input:ro" \
  -v "$(pwd)/data:/app/data" \
  sharepoint-rag-pipeline:latest
```

### 3️⃣ Ergebnisse prüfen
```bash
# Verarbeitungsbericht ansehen
cat data/reports/latest_report.json | python -m json.tool

# Logs prüfen
make logs

# Web-Interface für Monitoring
make monitor  # http://localhost:8080
```

---

## 🎯 Typische Anwendungsfälle

### 1️⃣ Einmalige Verarbeitung
```bash
# Test-Lauf (zeigt nur, was verarbeitet würde)
make process-dry INPUT=/path/to/pdfs

# Echte Verarbeitung
make process INPUT=/path/to/pdfs

# Mit mehr Kontrolle
docker run --rm \
  -v "/path/to/pdfs:/app/input:ro" \
  -v "$(pwd)/data:/app/data" \
  -e MAX_WORKERS=2 \
  -e MIN_QUALITY_SCORE=80 \
  sharepoint-rag-pipeline:latest
```

### 2️⃣ Monatliche Automatisierung
```bash
# Scheduler einrichten
echo "CRON_SCHEDULE=0 2 1 * *" >> .env  # Jeden 1. des Monats um 2:00
make run-scheduled

# Status prüfen
make status
make logs-scheduler
```

### 3️⃣ Development/Testing
```bash
# Entwicklungsumgebung starten
make setup-dev
make run-dev

# Tests ausführen
make test-all

# Jupyter Notebook für Analyse
make jupyter  # http://localhost:8888
```

### 4️⃣ Monitoring & Debugging
```bash
make help              # Alle verfügbaren Befehle
make logs             # Live-Logs anzeigen
make status           # Container-Status
make health           # Health-Check ausführen
make stats            # Resource-Usage
```

---

## ⚙️ Wichtige Einstellungen

### Environment Variables (.env)
```bash
# Wichtigste Einstellungen
INPUT_DIR=/path/to/sharepoint/pdfs    # Ihr PDF-Verzeichnis
MAX_WORKERS=4                         # Anzahl parallele Worker
MIN_QUALITY_SCORE=70                  # Qualitätsschwelle (0-100)
CRON_SCHEDULE=0 2 1 * *              # Monatlich um 2:00 Uhr

# Optional
OPENAI_API_KEY=your-api-key          # Für erweiterte AI-Features
LOG_LEVEL=INFO                       # DEBUG für mehr Details
```

### Performance-Tuning
```bash
# Für mehr Geschwindigkeit (mehr RAM benötigt)
docker run -e MAX_WORKERS=8 sharepoint-rag-pipeline:latest

# Für weniger RAM-Verbrauch
docker run -e MAX_WORKERS=2 --memory=2g sharepoint-rag-pipeline:latest

# Mit GPU-Beschleunigung (falls verfügbar)
docker run --gpus all sharepoint-rag-pipeline:gpu
```

### Chunk-Einstellungen (config/pipeline.yaml)
```yaml
chunking:
  chunk_size: 1000        # Token pro Chunk
  chunk_overlap: 200      # Überlappung zwischen Chunks
  strategy: "contextual"   # Intelligente Segmentierung

quality_validation:
  min_quality_score: 70   # Qualitätsschwelle
  check_completeness: true
```

---

## 🔥 Häufige Probleme & 30-Sekunden-Fixes

### "Permission denied" bei Docker
```bash
# Lösung 1: Docker-Gruppe beitreten
sudo usermod -aG docker $USER
newgrp docker

# Lösung 2: Ownership korrigieren
sudo chown -R $USER:$USER ./data

# Lösung 3: Mit sudo
sudo make process INPUT=/path/to/pdfs
```

### "Out of memory" Fehler
```bash
# Memory-Limit erhöhen
docker run --memory=8g sharepoint-rag-pipeline:latest

# Weniger Worker
make process INPUT=/path MAX_WORKERS=2

# Swap aktivieren (Linux)
sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
```

### "File not found" bei Volumes
```bash
# ❌ Falsch (relative Pfade):
docker run -v "./pdfs:/app/input" ...

# ✅ Richtig (absolute Pfade):
docker run -v "/home/user/pdfs:/app/input" ...
docker run -v "$(pwd)/pdfs:/app/input" ...
make process INPUT=/absolute/path/to/pdfs
```

### Langsame Verarbeitung
```bash
# CPU-Auslastung prüfen
make stats

# Logs auf Fehler prüfen
make logs | grep ERROR

# Performance-Test
make test-performance
```

### ChromaDB Connection Error
```bash
# Kein Problem! Pipeline nutzt automatisch JSON-Fallback
# Oder explizit ChromaDB starten:
docker-compose --profile external-db up -d chromadb
```

---

## 🔬 Was passiert bei der Verarbeitung?

### Pipeline-Phasen
1. **📄 Multi-Backend PDF-Extraktion**: PyMuPDF → pdfplumber → PyPDF2 (Fallback-Chain)
2. **📝 Intelligente Metadaten-Analyse**: Titel, Autoren, Datum, Dokumenttyp
3. **✂️ Contextual Chunking**: Hierarchie-bewusste Segmentierung
4. **🧠 Context Enrichment**: 
   - Dokumenthierarchie (Kapitel → Sektion → Subsektionen)
   - Navigationskontext (Previous/Next/Related chunks)
   - Semantische Rollen (Main content, Prerequisites, etc.)
   - NLP-basierte Konzeptextraktion
5. **✅ 7-stufige Qualitätsprüfung**: Vollständigkeit, Kohärenz, Informationsdichte
6. **💾 Dual Storage**: ChromaDB (Vektoren) + SQLite (Metadaten) + JSON-Fallback

### Technische Features
- **Incremental Processing**: Hash-basierte Änderungserkennung
- **Fault Tolerance**: Automatische Fallback-Modi bei Komponentenfehlern
- **Rich Metadata**: Vollständige Kontext-Information pro Chunk
- **Quality Scoring**: 0-100 Bewertung für jeden Chunk

**Ergebnis**: Production-ready Contextual RAG mit maximaler Robustheit! 🚀

---

## 📈 Beispiel-Output

### Console Output
```
🚀 SharePoint RAG Pipeline v2.0.0
📁 Processing /data/sharepoint/pdfs
📊 Found 42 PDF files (3 new, 39 unchanged)

[===================] 100% | 42/42 files | ETA: 00:00

✅ PROCESSING COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total files: 42
Processed: 40 ✅ | Failed: 2 ❌
Chunks created: 2,456 (avg: 61.4 per doc)
Quality score: 87.3 ± 12.1 (min: 65, max: 98)
Processing time: 4m 12s (1.7 files/min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Report JSON (data/reports/latest_report.json)
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "summary": {
    "total_files_processed": 42,
    "successful": 40,
    "failed": 2,
    "total_chunks_created": 2456,
    "average_quality_score": 87.3,
    "processing_time_seconds": 252.1
  },
  "performance": {
    "files_per_minute": 10.0,
    "chunks_per_second": 9.8,
    "memory_peak_mb": 2048,
    "storage_used_mb": 145.7
  },
  "quality_distribution": {
    "excellent": 23,  // 90-100
    "good": 15,       // 70-89
    "acceptable": 2,  // 50-69
    "poor": 0         // < 50
  }
}
```

---

## 📁 Output erklärt

```
data/
├── vectors/              # 🧠 Vektor-Embeddings
│   ├── chroma.sqlite3   # ChromaDB (primär)
│   └── fallback/        # JSON-Fallback
├── metadata/            # 📊 Metadaten
│   └── metadata.db      # SQLite mit allen Infos
├── state/               # 🔄 Processing State
│   └── file_hashes.json # Für incremental updates
├── reports/             # 📈 Berichte
│   ├── latest_report.json
│   └── archive/         # Historische Reports
└── logs/                # 📝 Detaillierte Logs
    └── contextual_pipeline.log
```

### Projektstruktur (Vollständig)
```
sharepoint-rag-pipeline/
├── 🐳 Docker Files
│   ├── Dockerfile              # Multi-stage Container
│   ├── docker-compose.yml      # Services & Orchestrierung
│   ├── .env.example           # Environment Template
│   └── Makefile               # 40+ vereinfachte Commands
├── 🏗️ Source Code
│   ├── src/agents/            # AutoGen Agenten
│   ├── src/pipeline/          # Pipeline-Orchestrierung
│   ├── src/models/            # Datenmodelle
│   └── src/storage/           # Speicher-Backend
├── ⚙️ Configuration
│   ├── config/pipeline.yaml   # Hauptkonfiguration
│   └── config/context_rules.yaml # Kontext-Regeln
├── 🚀 Main Scripts
│   ├── run_pipeline.py        # Hauptskript
│   └── test_pipeline.py       # Test & Validierung
└── 📚 Documentation
    ├── QUICKSTART.md          # Diese Datei
    ├── DOCKER.md              # Container-Guide
    └── INSTALLATION.md        # Vollständige Installation
```

---

## 🚀 Produktiv-Deployment

### Automatisierung einrichten
```bash
# Docker-Scheduler (empfohlen)
echo "CRON_SCHEDULE=0 2 1 * *" >> .env  # Monatlich
docker-compose --profile scheduled up -d rag-scheduler

# Oder systemweiter Cron-Job
sudo crontab -e
# Zeile hinzufügen:
0 2 1 * * cd /opt/sharepoint-rag-pipeline && make process INPUT=/data/sharepoint/pdfs
```

### Monitoring & Alerting
```bash
# Web-Dashboard starten
make monitor  # http://localhost:8080

# Health-Check Endpoint
curl http://localhost:8000/health

# E-Mail Benachrichtigungen (Linux)
make process INPUT=/data/pdfs && \
  mail -s "✅ RAG Pipeline Success" admin@company.com < data/reports/latest_report.json
```

### Cloud-Deployment
```bash
# Image für Registry bauen
docker build -t your-registry.com/rag-pipeline:v1.0 .
docker push your-registry.com/rag-pipeline:v1.0

# Kubernetes deployment
kubectl apply -f k8s-deployment.yaml

# Docker Swarm
docker stack deploy -c docker-compose.yml rag-stack
```

---

## ⚡ Performance & Optimierung

### 🚀 Geschwindigkeit optimieren
```bash
# Mehr Worker (CPU-intensive Aufgaben)
make process INPUT=/path/to/pdfs
docker run -e MAX_WORKERS=8 sharepoint-rag-pipeline:latest

# GPU-Beschleunigung (falls verfügbar)
docker run --gpus all sharepoint-rag-pipeline:gpu
```

### 💾 Speicher optimieren
```bash
# Weniger Worker bei begrenztem RAM
docker run -e MAX_WORKERS=2 --memory=2g sharepoint-rag-pipeline:latest

# Chunk-Größe reduzieren
docker run -e CHUNK_SIZE=500 -e CHUNK_OVERLAP=100 sharepoint-rag-pipeline:latest
```

### ⚖️ Qualität vs. Geschwindigkeit
```bash
# Hohe Qualität (langsamer)
docker run -e MIN_QUALITY_SCORE=90 sharepoint-rag-pipeline:latest

# Schnelle Verarbeitung (niedrigere Standards)
docker run -e MIN_QUALITY_SCORE=60 -e SKIP_OCR=true sharepoint-rag-pipeline:latest
```

### 📊 Benchmark-Zahlen
| Dokumente | Worker | Zeit | RAM |
|-----------|--------|------|-----|
| 10 PDFs | 4 | ~2 min | 1.5 GB |
| 100 PDFs | 4 | ~15 min | 2.5 GB |
| 100 PDFs | 8 | ~8 min | 4 GB |
| 1000 PDFs | 4 | ~2.5 h | 4 GB |

---

## 🎓 Weiterführende Ressourcen

📚 **Dokumentation**
- [DOCKER.md](DOCKER.md) - Vollständiger Container-Guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problemlösungen
- [ARCHITECTURE.md](ARCHITECTURE.md) - System-Design
- [API.md](API.md) - Entwickler-Referenz

🛠️ **Tools & Integration**
- [Makefile](Makefile) - Alle Befehle im Überblick
- [docker-compose.yml](docker-compose.yml) - Service-Konfiguration
- [config/](config/) - Anpassbare Einstellungen

💬 **Support**
- GitHub Issues für Bug Reports
- Discussions für Fragen
- Wiki für Community-Beiträge

---

## 🎉 Ready to Go!

**Herzlichen Glückwunsch!** Sie haben die SharePoint RAG Pipeline erfolgreich eingerichtet!

Die Pipeline verarbeitet nun Ihre Dokumente mit fortschrittlicher Kontext-Anreicherung und ist bereit für den produktiven Einsatz.

### 🚀 Immediate Next Steps
1. 📁 PDFs in Ihr Verzeichnis legen
2. 🏃 `make process INPUT=/path/to/pdfs` ausführen
3. 📊 Ergebnisse in `data/reports/` prüfen
4. 🔍 ChromaDB für RAG-Abfragen nutzen
5. 📈 Monitoring Dashboard aufrufen: `make monitor`

**Happy Processing!** 🚀📄➡️🧠