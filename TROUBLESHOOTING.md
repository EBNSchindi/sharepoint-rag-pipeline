# 🚨 Troubleshooting Guide - SharePoint RAG Pipeline

**Schnelle Problemlösung für alle gängigen Szenarien**

## 🆘 Notfall-Checkliste (3 Minuten)

```bash
# 1. Basis-Diagnose
make health
docker --version && docker-compose --version

# 2. Logs prüfen
make logs | tail -20

# 3. Container-Status
make status

# 4. Test ausführen
make test
```

**Wenn alle 4 Schritte erfolgreich sind, liegt das Problem wahrscheinlich in der Konfiguration.**

---

## 🐳 Docker-spezifische Probleme

### ❌ "Permission denied" beim Docker-Zugriff

**Symptom**: `Got permission denied while trying to connect to the Docker daemon socket`

```bash
# Lösung 1: Docker-Gruppe beitreten (empfohlen)
sudo usermod -aG docker $USER
newgrp docker
# Oder logout/login

# Lösung 2: Docker-Service neu starten
sudo systemctl restart docker

# Lösung 3: Als Sudo ausführen (nicht empfohlen)
sudo docker-compose up rag-pipeline

# Testen
docker run hello-world
```

### ❌ "bind: address already in use"

**Symptom**: Port-Konflikte bei Container-Start

```bash
# Problem identifizieren
netstat -tulpn | grep :8000
lsof -i :8000

# Lösung 1: Service beenden
sudo pkill -f "python.*8000"
docker stop $(docker ps -q --filter "publish=8000")

# Lösung 2: Anderen Port verwenden
# In docker-compose.yml:
ports:
  - "8001:8000"  # Statt 8000:8000

# Lösung 3: Port in .env ändern
echo "WEB_PORT=8001" >> .env
```

### ❌ "No space left on device"

**Symptom**: Docker kann Container nicht erstellen

```bash
# Docker-Speicher analysieren
docker system df
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Aufräumen
docker system prune -f
docker volume prune -f
docker image prune -a -f

# Speicherplatz prüfen
df -h
sudo du -sh /var/lib/docker

# Falls nötig: Docker Root verschieben
sudo systemctl stop docker
sudo mv /var/lib/docker /new/path/docker
sudo ln -s /new/path/docker /var/lib/docker
sudo systemctl start docker
```

### ❌ Volume Mount Probleme

**Symptom**: "No such file or directory" oder leere Mounts

```bash
# Häufigste Ursache: Relative Pfade
# ❌ Falsch:
docker run -v "./pdfs:/app/input" ...

# ✅ Richtig:
docker run -v "/home/user/pdfs:/app/input" ...
docker run -v "$(pwd)/pdfs:/app/input" ...

# SELinux-Probleme (Red Hat/CentOS)
docker run -v "/path/to/pdfs:/app/input:ro,Z" ...

# Ownership-Probleme
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

---

## 🔧 Installation & Dependencies

### ❌ "ModuleNotFoundError" (Native Python)

**Symptom**: `ModuleNotFoundError: No module named 'pydantic'`

```bash
# Lösung 1: Virtual Environment aktivieren
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Lösung 2: Dependencies neu installieren
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Lösung 3: Python-Version prüfen
python --version  # Sollte 3.8-3.12 sein

# Lösung 4: Fallback auf Docker
make setup
make process INPUT=/path/to/pdfs
```

### ❌ "spaCy model not found"

**Symptom**: `OSError: [E050] Can't find model 'en_core_web_sm'`

```bash
# Standard-Lösung
python -m spacy download en_core_web_sm

# Bei Network-Problemen
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0.tar.gz

# Für Offline-Installation
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0.tar.gz
pip install en_core_web_sm-3.6.0.tar.gz

# Fallback: Modell deaktivieren
export DISABLE_SPACY=true
```

### ❌ ChromaDB Connection Errors

**Symptom**: `Connection failed to ChromaDB`

```bash
# ✅ Kein Problem! Pipeline hat automatischen Fallback
# Sie sehen nur eine Warnung, aber die Verarbeitung läuft weiter

# Wenn Sie ChromaDB explizit nutzen wollen:
# Lösung 1: Externe ChromaDB starten
docker-compose --profile external-db up -d chromadb

# Lösung 2: ChromaDB neu installieren
pip uninstall chromadb
pip install chromadb>=0.4.0,<0.5.0

# Lösung 3: Im Docker nutzen (empfohlen)
make setup
```

---

## 💾 Memory & Performance Issues

### ❌ "Out of Memory" / "Killed by OOM"

**Symptom**: Container oder Prozess wird abgebrochen

```bash
# Sofortlösung: Weniger Worker
docker run -e MAX_WORKERS=2 --memory=2g sharepoint-rag-pipeline:latest
make process INPUT=/path MAX_WORKERS=2

# Memory-Monitoring
docker stats
htop  # Oder top

# System-Memory prüfen
free -h
cat /proc/meminfo | grep Available

# Swap aktivieren (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Docker Memory Limit erhöhen
# In docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 8G
```

### ❌ Langsame Verarbeitung

**Symptom**: Pipeline braucht sehr lange

```bash
# Diagnose 1: CPU-Auslastung prüfen
htop
docker stats

# Diagnose 2: Logs auf Fehler prüfen
make logs | grep -E "(ERROR|WARNING|FAIL)"

# Diagnose 3: Performance-Test
make test-performance

# Lösung 1: Mehr Worker (wenn genug RAM)
docker run -e MAX_WORKERS=8 sharepoint-rag-pipeline:latest

# Lösung 2: SSD für Data-Directory
sudo mount /dev/nvme0n1 /mnt/fast
ln -sfn /mnt/fast/data ./data

# Lösung 3: GPU-Beschleunigung (falls verfügbar)
docker run --gpus all sharepoint-rag-pipeline:gpu

# Lösung 4: Qualitäts-Standards senken
docker run -e MIN_QUALITY_SCORE=60 -e SKIP_OCR=true sharepoint-rag-pipeline:latest
```

---

## 📄 PDF Processing Issues

### ❌ "Failed to extract text from PDF"

**Symptom**: Einzelne PDFs können nicht verarbeitet werden

```bash
# Diagnose: PDF manuell testen
python -c "
import PyPDF2
with open('problem.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    print(f'Pages: {len(reader.pages)}')
    print(f'Text: {reader.pages[0].extract_text()[:100]}')
"

# Lösung 1: PDF reparieren
qpdf --check problem.pdf
qpdf --qdf problem.pdf repaired.pdf

# Lösung 2: OCR erzwingen
docker run -e FORCE_OCR=true sharepoint-rag-pipeline:latest

# Lösung 3: PDF konvertieren
pdftk problem.pdf output fixed.pdf
# Oder:
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -o fixed.pdf problem.pdf
```

### ❌ "OCR failed" / "Tesseract error"

**Symptom**: Gescannte PDFs können nicht verarbeitet werden

```bash
# Tesseract Installation prüfen (Docker)
docker run sharepoint-rag-pipeline:latest tesseract --version

# Tesseract Installation (Native)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-deu
# macOS:
brew install tesseract tesseract-lang
# Windows:
# Download von: https://github.com/UB-Mannheim/tesseract/wiki

# Sprache prüfen
tesseract --list-langs

# OCR manuell testen
tesseract problem.pdf output.txt -l deu
```

---

## 🔧 Configuration Issues

### ❌ "Config file not found"

**Symptom**: `FileNotFoundError: config/pipeline.yaml`

```bash
# Lösung 1: Standard-Config kopieren
cp config/pipeline.yaml.example config/pipeline.yaml

# Lösung 2: Config-Pfad prüfen
ls -la config/
find . -name "*.yaml" -type f

# Lösung 3: Mit absoluten Pfaden
python run_pipeline.py /path/to/pdfs --config /absolute/path/to/config.yaml
```

### ❌ Environment Variables werden ignoriert

**Symptom**: Einstellungen aus .env haben keine Wirkung

```bash
# .env Datei prüfen
cat .env
echo $INPUT_DIR

# .env in Docker prüfen
docker-compose config

# Manuell setzen
export MAX_WORKERS=4
export MIN_QUALITY_SCORE=80

# Docker run mit expliziten Vars
docker run -e MAX_WORKERS=4 -e MIN_QUALITY_SCORE=80 sharepoint-rag-pipeline:latest
```

---

## 🌐 Network & Connectivity

### ❌ "Connection timeout" / "DNS resolution failed"

**Symptom**: Downloads oder API-Calls funktionieren nicht

```bash
# DNS prüfen
nslookup google.com
ping 8.8.8.8

# Proxy-Einstellungen
export http_proxy=http://proxy.company.com:8080
export https_proxy=http://proxy.company.com:8080

# Docker mit Proxy
# In ~/.docker/config.json:
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.company.com:8080",
      "httpsProxy": "http://proxy.company.com:8080"
    }
  }
}

# Firewall prüfen
sudo ufw status
sudo iptables -L
```

---

## 🗄️ Storage & Database Issues

### ❌ "Database locked" / "SQLite error"

**Symptom**: Metadaten können nicht gespeichert werden

```bash
# SQLite-Datei prüfen
sqlite3 data/metadata/metadata.db ".schema"

# Lock-Datei entfernen
rm -f data/metadata/metadata.db-wal
rm -f data/metadata/metadata.db-shm

# Database reparieren
sqlite3 data/metadata/metadata.db "PRAGMA integrity_check;"

# Backup und Rebuild
cp data/metadata/metadata.db data/metadata/metadata.db.backup
sqlite3 data/metadata/metadata.db ".backup data/metadata/metadata_new.db"
mv data/metadata/metadata_new.db data/metadata/metadata.db
```

### ❌ "Vector store corruption"

**Symptom**: ChromaDB/Vector-Daten sind beschädigt

```bash
# Fallback-Modus erzwingen
export USE_JSON_FALLBACK=true

# Vector-Store neu erstellen
rm -rf data/vectors/
mkdir -p data/vectors/

# Mit Force-All neu verarbeiten
make process INPUT=/path/to/pdfs FORCE_ALL=true
```

---

## 🔍 Debugging & Diagnostics

### 📋 Vollständige System-Diagnose

```bash
#!/bin/bash
echo "🔍 SharePoint RAG Pipeline - System Diagnose"
echo "============================================"

echo "📅 Timestamp: $(date)"
echo "💻 System: $(uname -a)"
echo "🐳 Docker: $(docker --version)"
echo "🔧 Docker Compose: $(docker-compose --version)"
echo ""

echo "📁 Verzeichnisstruktur:"
ls -la
echo ""

echo "🔧 Environment Variables:"
env | grep -E "(DOCKER|MAX_|MIN_|INPUT_)" | sort
echo ""

echo "🐳 Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "📊 Speicherverbrauch:"
df -h
free -h
echo ""

echo "🧪 Pipeline Test:"
make test 2>&1 | tail -10
echo ""

echo "📝 Letzte Logs:"
make logs 2>&1 | tail -15
```

### 🚨 Debug-Modus aktivieren

```bash
# Ausführliche Logs
export LOG_LEVEL=DEBUG
make logs

# Python Debug-Modus
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Docker Debug
docker-compose --verbose up rag-pipeline

# Memory-Profiling
docker run --rm -v "$(pwd):/app" sharepoint-rag-pipeline:dev \
  python -m memory_profiler run_pipeline.py /app/test_input
```

---

## 🆘 Emergency Recovery

### 🔥 "Alles kaputt" - Nuclear Option

```bash
# 1. Alles stoppen
docker-compose down -v
docker system prune -a -f

# 2. Projekt-Zustand resetten
git status
git reset --hard HEAD
rm -rf data/

# 3. Frischer Start
make setup
make test

# 4. Backup restore (falls vorhanden)
make restore BACKUP=backup/rag-data-20231201.tar.gz
```

### 💾 Backup erstellen (Prävention)

```bash
# Automatisches Backup vor jeder Verarbeitung
make backup

# Manuelles Backup
tar czf "backup-$(date +%Y%m%d_%H%M%S).tar.gz" \
  data/ config/ .env

# Cloud-Backup (AWS S3 Beispiel)
aws s3 sync ./data/ s3://your-bucket/rag-pipeline-backup/
```

---

## 📞 Support-Informationen sammeln

### Wenn Sie Hilfe benötigen, sammeln Sie diese Informationen:

```bash
# System-Info
uname -a > debug_info.txt
docker --version >> debug_info.txt
docker-compose --version >> debug_info.txt
free -h >> debug_info.txt
df -h >> debug_info.txt

# Pipeline-Status
make test >> debug_info.txt 2>&1
make status >> debug_info.txt 2>&1

# Logs
make logs --tail=50 >> debug_info.txt 2>&1

# Config
cat .env >> debug_info.txt
cat config/pipeline.yaml >> debug_info.txt

# Komprimieren und teilen
tar czf support_debug_$(date +%Y%m%d_%H%M%S).tar.gz debug_info.txt data/logs/ config/
```

---

## 🔗 Hilfreiche Links

- **Docker Issues**: [Docker Troubleshooting](https://docs.docker.com/config/daemon/troubleshoot/)
- **Python Environment**: [venv Guide](https://docs.python.org/3/library/venv.html)
- **Memory Debugging**: [Linux Memory Management](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html)
- **PDF Issues**: [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)

---

## ✅ Troubleshooting Checkliste

- [ ] Docker läuft und ist zugänglich
- [ ] Genügend Speicherplatz verfügbar (min. 5GB)
- [ ] RAM ausreichend (min. 2GB für kleine Dokumente)
- [ ] .env Datei existiert und ist konfiguriert
- [ ] PDF-Verzeichnis existiert und ist lesbar
- [ ] Ports 8000, 8080 sind verfügbar
- [ ] Internetverbindung für Downloads verfügbar
- [ ] `make test` läuft erfolgreich durch

**Bei persistenten Problemen**: GitHub Issues erstellen mit debug_info.txt