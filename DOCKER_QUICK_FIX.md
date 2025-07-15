# 🔧 Docker Quick Fix Guide

## Problem gelöst: Dependency Resolution Error

Die ursprüngliche `requirements.txt` hatte zu komplexe Dependencies. Ich habe das Problem wie folgt gelöst:

### ✅ Lösung 1: Fixierte Versionen

**Neue Datei-Struktur:**
```
requirements.txt         # Basis-Version mit fixen Versionen
requirements-minimal.txt # Nur PDF-Verarbeitung
requirements-full.txt    # Vollständige AI/ML-Version
```

### ✅ Lösung 2: Mehrstufige Docker-Installation

**Dockerfile jetzt mit Build-Argumenten:**
```dockerfile
ARG BUILD_MODE=full
ARG INSTALL_AI_DEPS=true
```

### 🚀 Verwendung:

#### Schnelle Installation (nur PDF-Verarbeitung):
```bash
# Für Docker-Berechtigungen (einmalig):
sudo usermod -aG docker $USER
newgrp docker

# Minimal-Build (5-10 Minuten):
make build-minimal

# Testen:
make process INPUT=/home/vboxuser/Documents/Wikipedia_File
```

#### Vollständige Installation (mit AI/ML):
```bash
# Vollständiger Build (15-30 Minuten):
make build

# Ohne AI/ML aber mit anderen Features:
make build-no-ai
```

### 📋 Test-Befehle:

```bash
# 1. Docker-Berechtigung testen
docker run hello-world

# 2. Minimal-Build testen
make build-minimal

# 3. Pipeline mit deiner Wikipedia-PDF testen
make process INPUT=/home/vboxuser/Documents/Wikipedia_File

# 4. Logs anzeigen
make logs
```

### 🔍 Für den aktuellen Benutzer:

```bash
# Schritt 1: Docker-Gruppe hinzufügen (braucht sudo - einmalig)
sudo usermod -aG docker $USER

# Schritt 2: Neue Gruppe laden (ohne Neustart)
newgrp docker

# Schritt 3: Test
docker run hello-world

# Schritt 4: Pipeline bauen
make build-minimal

# Schritt 5: Pipeline ausführen
make process INPUT=/home/vboxuser/Documents/Wikipedia_File
```

## Unterschiede der Build-Modi:

| Build-Modus | Installationszeit | Größe | Features |
|-------------|------------------|-------|----------|
| `minimal` | 5-10 min | ~2GB | PDF-Verarbeitung |
| `no-ai` | 10-15 min | ~3GB | PDF + ChromaDB |
| `full` | 15-30 min | ~5GB | Alles inkl. AI/ML |

## Fehlerbehebung:

### "Permission denied" → Docker-Gruppe
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "Build failed" → Minimal-Version versuchen
```bash
make build-minimal
```

### "No such file" → Verzeichnis prüfen
```bash
ls -la /home/vboxuser/Documents/Wikipedia_File/
```

Die Pipeline sollte jetzt ohne Dependency-Konflikte funktionieren! 🎉