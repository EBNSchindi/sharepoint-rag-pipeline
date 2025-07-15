# 🐳 Docker Platform Guide

## Quick Platform Setup

### 🪟 Windows
```powershell
# Install Docker Desktop
winget install Docker.DockerDesktop

# Setup pipeline
cd sharepoint-rag-pipeline
make setup-windows
cp .env.example .env
# Edit .env: INPUT_DIR=C:\Users\YourName\Documents\PDFs
make build
make process INPUT="C:\Users\YourName\Documents\PDFs"
```

### 🐧 Linux 
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Setup pipeline
cd sharepoint-rag-pipeline
make setup-linux
cp .env.example .env
# Edit .env: INPUT_DIR=/home/user/Documents/pdfs
make build
make process INPUT=/home/user/Documents/pdfs
```

### 🍎 macOS
```bash
# Install Docker Desktop
brew install --cask docker

# Setup pipeline
cd sharepoint-rag-pipeline
make setup-macos
cp .env.example .env
# Edit .env: INPUT_DIR=/Users/username/Documents/PDFs
make build
make process INPUT=/Users/username/Documents/PDFs
```

## Platform-Specific Notes

### Windows
- Use backslashes in .env paths: `INPUT_DIR=C:\Users\Name\Documents\PDFs`
- Enable WSL2 backend for better performance
- Share drives in Docker Desktop settings
- Use PowerShell or Command Prompt

### Linux
- Add user to docker group: `sudo usermod -aG docker $USER`
- Log out and back in after group change
- Use forward slashes: `INPUT_DIR=/home/user/Documents/pdfs`

### macOS
- Allocate sufficient resources in Docker Desktop
- Use forward slashes: `INPUT_DIR=/Users/username/Documents/PDFs`
- Consider using Rosetta 2 emulation for M1/M2 Macs if needed

## Common Issues

### Permission Denied (Linux)
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Volume Mount Failed (Windows)
- Check Docker Desktop → Settings → Resources → File Sharing
- Ensure C:\ drive is shared

### Out of Memory
- Increase Docker Desktop memory allocation
- Reduce MAX_WORKERS in .env
- Use smaller batch sizes

## Performance Tips

### Windows
- Use WSL2 backend
- Store project files in WSL2 filesystem for better performance
- Consider using `\\wsl$\Ubuntu\home\user\project\` paths

### Linux
- Use overlay2 storage driver
- Consider using bind mounts for better performance
- Monitor Docker space usage: `docker system df`

### macOS
- Increase Docker Desktop memory to 8GB+
- Use cached consistency for volumes on Apple Silicon
- Consider using Docker Desktop alternatives like Podman

## Troubleshooting Commands

```bash
# Check Docker installation
docker --version
docker compose --version

# Test Docker access
docker run hello-world

# Check container logs
docker compose logs rag-pipeline

# Monitor resource usage
docker stats

# Clean up Docker resources
docker system prune -a --volumes
```