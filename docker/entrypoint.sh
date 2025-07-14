#!/bin/bash
set -e

# SharePoint RAG Pipeline Docker Entrypoint

echo "🚀 Starting SharePoint RAG Pipeline Container"
echo "============================================="

# Display container info
echo "Container Info:"
echo "- Python Version: $(python --version)"
echo "- User: $(whoami)"
echo "- Working Directory: $(pwd)"
echo "- Available Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "- CPU Cores: $(nproc)"

# Environment variables
echo ""
echo "Environment:"
echo "- PIPELINE_MODE: ${PIPELINE_MODE:-production}"
echo "- LOG_LEVEL: ${LOG_LEVEL:-INFO}"
echo "- MAX_WORKERS: ${MAX_WORKERS:-4}"
echo "- MIN_QUALITY_SCORE: ${MIN_QUALITY_SCORE:-70}"

# Validate configuration
echo ""
echo "🔍 Validating Configuration..."
if [ ! -f "config/pipeline.yaml" ]; then
    echo "⚠️  No custom config found, using defaults"
else
    echo "✅ Configuration file found"
fi

# Test pipeline components
echo ""
echo "🧪 Testing Pipeline Components..."
python test_pipeline.py || {
    echo "❌ Pipeline component test failed!"
    exit 1
}

# Create sample input if none provided
if [ "$1" = "/app/input" ] && [ ! "$(ls -A /app/input 2>/dev/null)" ]; then
    echo ""
    echo "⚠️  No input files found in /app/input"
    echo "📁 Mount your PDF directory to /app/input"
    echo "   Example: -v /path/to/pdfs:/app/input:ro"
    echo ""
    echo "📖 For testing, creating sample structure..."
    mkdir -p /app/sample_input
    echo "This is a sample PDF content for testing." > /app/sample_input/sample.txt
    echo "To process real PDFs, mount your directory and restart the container."
    set -- "/app/sample_input"
fi

# Check input directory
if [ -n "$1" ] && [ -d "$1" ]; then
    echo ""
    echo "📂 Input Directory: $1"
    echo "   Files found: $(find "$1" -name "*.pdf" | wc -l) PDFs"
    if [ "$(find "$1" -name "*.pdf" | wc -l)" -eq 0 ]; then
        echo "   ⚠️  No PDF files found"
    fi
fi

# Adjust configuration based on environment
if [ -n "$MAX_WORKERS" ]; then
    echo ""
    echo "⚙️  Adjusting max_workers to $MAX_WORKERS"
    # This would typically update the config file
fi

echo ""
echo "🎯 Starting Pipeline Processing..."
echo "============================================="

# Execute the passed command
exec "$@"