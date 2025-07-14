# Multi-stage build for SharePoint RAG Pipeline
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    curl \
    git \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Download spaCy models
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download de_core_news_sm

# Production stage
FROM base as production

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p data/{input,processed,state,vectors,reports,backups} logs && \
    chown -R appuser:appuser data logs

# Make scripts executable
RUN chmod +x run_pipeline.py test_pipeline.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python test_pipeline.py || exit 1

# Switch to non-root user
USER appuser

# Expose port for potential web interface
EXPOSE 8000

# Default command
CMD ["python", "run_pipeline.py", "--help"]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython \
    jupyter

# Copy application code
COPY --chown=appuser:appuser . .

# Create directories
RUN mkdir -p data/{input,processed,state,vectors,reports,backups} logs && \
    chown -R appuser:appuser data logs

# Make scripts executable
RUN chmod +x run_pipeline.py test_pipeline.py

USER appuser

CMD ["bash"]