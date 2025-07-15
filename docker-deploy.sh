#!/bin/bash

# Docker Deployment Script with Permission Fixes
# This script handles Docker deployment with proper permission management

echo "🚀 Docker Deployment Script"
echo "============================"

# Check if running as root (not recommended but might be needed)
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root - this is not recommended"
    echo "Consider running as regular user with docker group membership"
fi

# Create docker-compose command wrapper
if ! command -v docker-compose &> /dev/null; then
    echo "📝 Creating docker-compose wrapper..."
    cat > /tmp/docker-compose << 'EOF'
#!/bin/bash
docker compose "$@"
EOF
    chmod +x /tmp/docker-compose
    export PATH="/tmp:$PATH"
    echo "✅ docker-compose wrapper created"
fi

# Function to fix permissions
fix_permissions() {
    echo "🔧 Fixing file permissions..."
    
    # Fix input directory
    chmod 755 ./sample_input/ 2>/dev/null || true
    chmod 644 ./sample_input/*.pdf 2>/dev/null || true
    
    # Create and fix data directories
    mkdir -p data/{input,processed,state,vectors,reports,backups}
    mkdir -p logs
    chmod -R 755 data logs
    
    # Fix Docker-related files
    chmod 644 docker-compose.yml Dockerfile .env 2>/dev/null || true
    chmod 755 run_pipeline.py test_pipeline.py 2>/dev/null || true
    
    echo "✅ Permissions fixed"
}

# Function to build Docker image
build_image() {
    echo "🏗️  Building Docker image..."
    
    # Build with proper user mapping
    docker build \
        --build-arg USER_ID=$(id -u) \
        --build-arg GROUP_ID=$(id -g) \
        -t sharepoint-rag-pipeline:latest \
        --target production \
        . || {
        echo "❌ Build failed"
        return 1
    }
    
    echo "✅ Docker image built successfully"
}

# Function to run container
run_container() {
    echo "🚀 Starting RAG Pipeline container..."
    
    # Stop existing container if running
    docker stop rag-pipeline 2>/dev/null || true
    docker rm rag-pipeline 2>/dev/null || true
    
    # Run container with proper volume mounts and permissions
    docker run \
        --name rag-pipeline \
        --user $(id -u):$(id -g) \
        -v "$(pwd)/sample_input:/app/input:ro" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/config:/app/config:ro" \
        -e LOG_LEVEL=INFO \
        -e MAX_WORKERS=2 \
        --rm \
        sharepoint-rag-pipeline:latest \
        python run_pipeline.py /app/input --workers 2 --verbose
}

# Function to run with docker-compose
run_compose() {
    echo "🐳 Starting with docker-compose..."
    
    # Use docker compose (newer syntax)
    docker compose down 2>/dev/null || true
    docker compose build --no-cache
    docker compose up rag-pipeline
}

# Main execution
main() {
    echo "Current user: $(whoami) ($(id))"
    echo "Docker version: $(docker --version 2>/dev/null || echo 'Docker not accessible')"
    
    fix_permissions
    
    echo ""
    echo "Choose deployment method:"
    echo "1. Direct docker run (recommended for testing)"
    echo "2. Docker compose (recommended for production)"
    echo ""
    
    # For non-interactive mode, default to docker run
    if [[ -t 0 ]]; then
        read -p "Enter choice (1 or 2): " choice
    else
        choice=1
        echo "Running in non-interactive mode, using docker run..."
    fi
    
    case $choice in
        1)
            build_image && run_container
            ;;
        2)
            run_compose
            ;;
        *)
            echo "Invalid choice, defaulting to docker run"
            build_image && run_container
            ;;
    esac
}

# Run main function
main "$@"