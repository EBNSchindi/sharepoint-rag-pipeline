#!/bin/bash

# Docker Permission Fix Script
# This script fixes common Docker permission issues

echo "🔧 Docker Permission Fix Script"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running or no permissions"
    echo "Please run: sudo systemctl start docker"
    echo "Then add user to docker group: sudo usermod -aG docker $USER"
    echo "Then logout and login again"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found"
    echo "Using docker compose plugin instead..."
    
    # Create docker-compose wrapper
    cat > docker-compose << 'EOF'
#!/bin/bash
docker compose "$@"
EOF
    chmod +x docker-compose
    export PATH="$PWD:$PATH"
    echo "✅ Created docker-compose wrapper"
fi

# Fix directory permissions
echo "🔧 Fixing directory permissions..."
chmod 755 ./sample_input/
chmod 644 ./sample_input/*.pdf 2>/dev/null || true

# Create data directories with proper permissions
mkdir -p data/{input,processed,state,vectors,reports,backups}
mkdir -p logs
chmod -R 755 data logs

echo "✅ Permission fix completed!"
echo ""
echo "Next steps:"
echo "1. Run: docker compose build --no-cache"
echo "2. Run: docker compose up rag-pipeline"