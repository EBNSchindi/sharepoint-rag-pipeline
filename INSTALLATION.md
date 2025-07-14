# Installation und Setup Guide

## 🚀 Schnellstart (5 Minuten)

**Für den sofortigen Einstieg siehe: [QUICKSTART.md](QUICKSTART.md)**

## Systemanforderungen

**Minimum:**
- Python 3.8+
- 4GB RAM
- 2GB freier Speicherplatz
- Linux/macOS/Windows

**Empfohlen:**
- Python 3.10+
- 8GB RAM
- 5GB freier Speicherplatz
- SSD-Speicher

## Schritt-für-Schritt Installation

### 1. Voraussetzungen prüfen

```bash
# Python Version (3.8+)
python3 --version

# Pip verfügbar
python3 -m pip --version

# Verfügbarer Speicherplatz (mindestens 2GB)
df -h
```

### 2. Virtuelle Umgebung einrichten

```bash
# In das Projektverzeichnis wechseln
cd sharepoint-rag-pipeline

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Pip aktualisieren
pip install --upgrade pip
```

### 3. Dependencies installieren

```bash
# Core Dependencies
pip install -r requirements.txt

# spaCy Sprachmodell (Englisch)
python -m spacy download en_core_web_sm

# Optional: Deutsches Modell
python -m spacy download de_core_news_sm
```

### 4. Installation validieren

```bash
# Pipeline-Komponenten testen
python test_pipeline.py

# Erwartete Ausgabe:
# ✅ Configuration loaded successfully
# ✅ Metadata Store initialized
# ✅ Incremental Processor
# ...

# Hauptskript testen
python run_pipeline.py --help
```

### 5. Erste Konfiguration

```bash
# Konfiguration anpassen (optional)
cp config/pipeline.yaml config/pipeline.yaml.backup
nano config/pipeline.yaml
```

**Wichtige Einstellungen:**

```yaml
# Anzahl parallel verarbeiteter Dateien (an CPU-Kerne anpassen)
processing:
  max_workers: 4

# Chunk-Größe für RAG
chunking:
  chunk_size: 1000    # Token pro Chunk
  chunk_overlap: 200  # Überlappung

# Qualitäts-Schwellenwerte
quality_validation:
  min_quality_score: 70  # 0-100
```

## Erweiterte Installation

### OCR-Unterstützung (für gescannte PDFs)

```bash
# Tesseract installieren
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# macOS:
brew install tesseract

# Windows: Download von https://github.com/UB-Mannheim/tesseract/wiki

# Python-Bindings
pip install pytesseract
```

### Performance-Optimierung

```bash
# GPU-Unterstützung für Transformers (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Faster JSON parsing
pip install ujson

# Memory profiling für Debugging
pip install memory-profiler
```

### Zusätzliche Sprachmodelle

```bash
# Weitere spaCy Modelle
python -m spacy download de_core_news_lg  # Deutsch (groß)
python -m spacy download en_core_web_lg   # Englisch (groß)

# Transformers Modelle werden automatisch heruntergeladen
```

## Verifikation und Tests

### 1. Komponenten-Test

```bash
# Umfassender Test aller Komponenten
python test_pipeline.py

# Bei Erfolg sollten Sie sehen:
# ✅ Configuration loaded successfully
# ✅ Metadata Store - 0 documents
# ✅ Incremental Processor
# ✅ Context Rules loaded
```

### 2. Test mit echten Dokumenten

```bash
# Test-Verzeichnis erstellen
mkdir test_input

# Ein oder mehrere PDFs in test_input/ ablegen
# Dann Pipeline testen:

# Dry run (zeigt was verarbeitet würde)
python run_pipeline.py test_input --dry-run

# Echte Verarbeitung
python run_pipeline.py test_input --force-all

# Erwartete Ausgabe:
# ========================================
# PROCESSING COMPLETED
# ========================================
# Total files processed: 1
# Successful: 1
# Failed: 0
# Total chunks created: 15+
```

### 3. Qualitätsprüfung

```bash
# Verarbeitungsbericht prüfen
cat data/reports/latest_report.json

# Logs prüfen
tail -f logs/contextual_pipeline.log

# Datenbank-Statistiken
python -c "
import sys; sys.path.insert(0, 'src')
from storage.metadata_store import MetadataStore
store = MetadataStore({'metadata_db_path': 'data/metadata.db'})
print('Statistiken:', store.get_statistics())
"
```

## Häufige Installationsprobleme

### Problem: "ModuleNotFoundError"

**Ursache:** Virtuelle Umgebung nicht aktiviert oder Dependencies nicht installiert

**Lösung:**
```bash
# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Dependencies neu installieren
pip install -r requirements.txt

# Python-Path prüfen
python -c "import sys; print('Python Path:', sys.path[:3])"
```

### Problem: "spaCy model not found"

**Ursache:** Sprachmodell nicht installiert

**Lösung:**
```bash
# Modell installieren
python -m spacy download en_core_web_sm

# Verfügbare Modelle prüfen
python -m spacy info

# Manueller Download (falls nötig)
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0.tar.gz
```

### Problem: "ChromaDB initialization failed"

**Ursache:** ChromaDB Kompatibilitätsprobleme

**Lösung:**
```bash
# ChromaDB neu installieren
pip uninstall chromadb
pip install chromadb>=0.4.0

# Oder: Fallback verwenden (automatisch aktiviert)
# Pipeline funktioniert auch ohne ChromaDB mit JSON-Fallback
```

### Problem: "Permission denied"

**Ursache:** Datei-/Verzeichnisberechtigungen

**Lösung:**
```bash
# Berechtigungen korrigieren
chmod +x run_pipeline.py test_pipeline.py
chmod -R 755 src/
chmod -R 700 data/

# Für andere User
sudo chown -R $USER:$USER sharepoint-rag-pipeline/
```

### Problem: "Out of memory"

**Ursache:** Zu wenig RAM oder zu große Dokumente

**Lösung:**
```bash
# Weniger Worker verwenden
python run_pipeline.py /path/to/pdfs --workers 2

# Konfiguration anpassen
nano config/pipeline.yaml
# processing:
#   batch_size: 5
#   max_workers: 2
# performance:
#   memory_limit_mb: 1024
```

### Problem: "AutoGen/OpenAI API Fehler"

**Ursache:** API-Schlüssel oder AutoGen-Konfiguration

**Lösung:**
```bash
# AutoGen ist optional - Pipeline funktioniert mit Fallback-Modi
# Für volle Funktionalität:
export OPENAI_API_KEY="your-api-key"

# Oder AutoGen-Komponenten deaktivieren in config/pipeline.yaml
```

## Erweiterte Konfiguration

### Datenbankoptimierung

```bash
# SQLite Performance verbessern
# In config/pipeline.yaml:
# metadata_db_path: "/fast/ssd/path/metadata.db"

# Oder PostgreSQL verwenden (erfordert Anpassungen)
pip install psycopg2-binary
```

### Memory Management

```yaml
# config/pipeline.yaml
performance:
  memory_limit_mb: 2048
  enable_parallel_processing: true
  chunk_batch_size: 50
  embedding_batch_size: 32
```

### Logging-Konfiguration

```yaml
# config/pipeline.yaml
logging:
  level: "INFO"        # DEBUG für detaillierte Logs
  file: "./logs/pipeline.log"
  rotate: true
  max_size_mb: 100
  backup_count: 5
```

## Produktionssetup

### 1. Systemd Service (Linux)

```bash
# Service-Datei erstellen
sudo nano /etc/systemd/system/rag-pipeline.service
```

```ini
[Unit]
Description=SharePoint RAG Pipeline
After=network.target

[Service]
Type=oneshot
User=raguser
Group=raguser
WorkingDirectory=/opt/sharepoint-rag-pipeline
Environment=PATH=/opt/sharepoint-rag-pipeline/venv/bin
ExecStart=/opt/sharepoint-rag-pipeline/venv/bin/python run_pipeline.py /data/sharepoint/documents
StandardOutput=journal
StandardError=journal
TimeoutSec=3600

[Install]
WantedBy=multi-user.target
```

```bash
# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable rag-pipeline.service

# Testen
sudo systemctl start rag-pipeline.service
sudo systemctl status rag-pipeline.service
```

### 2. Cron-Job Setup

```bash
# Crontab bearbeiten
crontab -e

# Monatliche Ausführung (1. jeden Monats um 2:00)
0 2 1 * * cd /opt/sharepoint-rag-pipeline && /opt/sharepoint-rag-pipeline/venv/bin/python run_pipeline.py /data/sharepoint/documents >> /var/log/rag-pipeline.log 2>&1

# Wöchentliche Ausführung (Sonntags um 3:00)  
0 3 * * 0 cd /opt/sharepoint-rag-pipeline && /opt/sharepoint-rag-pipeline/venv/bin/python run_pipeline.py /data/sharepoint/documents >> /var/log/rag-pipeline.log 2>&1
```

### 3. Monitoring und Alerting

```bash
# Log-Rotation einrichten
sudo nano /etc/logrotate.d/rag-pipeline
```

```
/var/log/rag-pipeline.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 0644 raguser raguser
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
```

### 4. Backup-Automatisierung

```bash
# Backup-Skript erstellen
nano backup_pipeline.sh
```

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backup/rag-pipeline/$(date +%Y%m%d_%H%M%S)"
PIPELINE_DIR="/opt/sharepoint-rag-pipeline"

mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR"

# Datenbank und Vektoren sichern
cp "$PIPELINE_DIR/data/metadata.db" "$BACKUP_DIR/" 2>/dev/null || echo "No metadata.db found"
cp -r "$PIPELINE_DIR/data/vectors" "$BACKUP_DIR/" 2>/dev/null || echo "No vectors found"
cp -r "$PIPELINE_DIR/data/state" "$BACKUP_DIR/" 2>/dev/null || echo "No state found"
cp -r "$PIPELINE_DIR/config" "$BACKUP_DIR/"

# Komprimieren
cd "$(dirname "$BACKUP_DIR")"
tar -czf "$(basename "$BACKUP_DIR").tar.gz" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

# Alte Backups löschen (älter als 30 Tage)
find /backup/rag-pipeline -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

```bash
chmod +x backup_pipeline.sh

# Tägliches Backup (nachts um 1:00)
echo "0 1 * * * /opt/sharepoint-rag-pipeline/backup_pipeline.sh" | crontab -
```

## Upgrade und Wartung

### Version Upgrade

```bash
# Aktuelle Umgebung sichern
pip freeze > requirements_old.txt
cp -r config config_backup_$(date +%Y%m%d)

# Neue Version installieren
git pull  # oder neue Dateien extrahieren
pip install -r requirements.txt --upgrade

# Migrationen ausführen (falls nötig)
python run_pipeline.py /path/to/test --validate-only

# Bei Problemen: Rollback
pip install -r requirements_old.txt
```

### Wartungsaufgaben

```bash
# Alte Logs bereinigen
find logs/ -name "*.log" -mtime +30 -delete

# Alte Berichte bereinigen  
find data/reports/ -name "*.json" -mtime +90 -delete

# Datenbank-Statistiken
python -c "
import sys; sys.path.insert(0, 'src')
from storage.metadata_store import MetadataStore
store = MetadataStore({'metadata_db_path': 'data/metadata.db'})
print('DB Stats:', store.get_statistics())
"

# Vector Store Statistiken (falls ChromaDB verfügbar)
python -c "
import sys; sys.path.insert(0, 'src')
from storage.vector_store import ContextualVectorStore
store = ContextualVectorStore({'vector_store': {'persist_directory': 'data/vectors'}})
print('Vector Stats:', store.get_collection_stats())
"
```

## Deinstallation

```bash
# 1. Services stoppen
sudo systemctl stop rag-pipeline.service
sudo systemctl disable rag-pipeline.service

# 2. Cron-Jobs entfernen
crontab -e
# Entsprechende Zeilen löschen

# 3. Virtuelle Umgebung deaktivieren
deactivate

# 4. Dateien entfernen
rm -rf sharepoint-rag-pipeline/

# 5. System-Services bereinigen (optional)
sudo rm /etc/systemd/system/rag-pipeline.service
sudo systemctl daemon-reload
sudo rm /etc/logrotate.d/rag-pipeline
```

## Support und Debugging

### Debugging-Tools

```bash
# Ausführlicher Test
python test_pipeline.py

# Verbose Pipeline-Ausführung
python run_pipeline.py /path/to/test --verbose

# Nur Validierung
python run_pipeline.py /path/to/test --validate-only

# Memory Profiling
python -m memory_profiler run_pipeline.py /path/to/small_test

# Systeminfo
python -c "
import sys, platform, psutil
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'RAM: {psutil.virtual_memory().total // (1024**3)}GB')
print(f'CPU Cores: {psutil.cpu_count()}')
"
```

### Log-Analyse

```bash
# Aktuelle Logs anzeigen
tail -f logs/contextual_pipeline.log

# Fehler suchen
grep -i error logs/contextual_pipeline.log

# Performance-Metriken
grep -i "processing time" logs/contextual_pipeline.log

# Qualitäts-Issues
grep -i "quality score" logs/contextual_pipeline.log
```

### Häufige Debugging-Befehle

```bash
# Dependencies prüfen
pip list | grep -E "(pydantic|autogen|chromadb|spacy|transformers)"

# Konfiguration validieren
python -c "import yaml; print(yaml.safe_load(open('config/pipeline.yaml')))"

# Datenbankzugriff testen
python -c "
import sqlite3
conn = sqlite3.connect('data/metadata.db')
print('Tables:', [r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()])
conn.close()
"

# Vector Store testen
python -c "
import sys; sys.path.insert(0, 'src')
from storage.vector_store import ContextualVectorStore
try:
    store = ContextualVectorStore({'vector_store': {'persist_directory': 'data/vectors'}})
    print('Vector Store OK')
except Exception as e:
    print(f'Vector Store Error: {e}')
"
```

Bei weiteren Problemen:

1. **Test-Pipeline ausführen**: `python test_pipeline.py`
2. **Logs prüfen**: `logs/contextual_pipeline.log`
3. **Minimal-Setup testen**: Mit einem einzelnen kleinen PDF
4. **Konfiguration überprüfen**: `config/pipeline.yaml`
5. **Dependencies validieren**: `pip list`