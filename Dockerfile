# Multi-stage build for SharePoint RAG Pipeline
FROM python:3.11-slim AS base

# Build arguments
ARG BUILD_MODE=full
ARG INSTALL_AI_DEPS=true

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BUILD_MODE=${BUILD_MODE}

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

# Create app user with flexible UID/GID
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN if [ "${GROUP_ID}" != "0" ]; then groupadd --gid ${GROUP_ID} appuser; fi && \
    if [ "${USER_ID}" != "0" ]; then \
        useradd --uid ${USER_ID} --gid ${GROUP_ID} --shell /bin/bash --create-home appuser; \
    else \
        echo "Running as root user"; \
    fi

# Set working directory
WORKDIR /app

# Install Python dependencies in stages to avoid conflicts
COPY requirements.txt requirements-minimal.txt requirements-full.txt ./

# Stage 1: Install core dependencies based on build mode
RUN pip install --upgrade pip && \
    if [ "$BUILD_MODE" = "minimal" ]; then \
        echo "Installing minimal dependencies..." && \
        pip install -r requirements-minimal.txt; \
    else \
        echo "Installing full dependencies..." && \
        pip install -r requirements.txt; \
    fi

# Stage 2: Install AI/ML dependencies (only if enabled and in full mode)
RUN if [ "$BUILD_MODE" = "full" ] && [ "$INSTALL_AI_DEPS" = "true" ]; then \
        echo "Installing AI/ML dependencies..." && \
        pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu && \
        pip install sentence-transformers==5.0.0 && \
        pip install spacy==3.8.7 && \
        pip install transformers==4.53.2 && \
        pip install chromadb==0.4.24 && \
        pip install pyautogen==0.10.0 && \
        pip install scikit-learn==1.7.0 && \
        pip install scipy==1.16.0; \
    else \
        echo "Skipping AI/ML dependencies"; \
    fi

# Download spaCy models (only if spacy is installed)
RUN python -c "import spacy; print('spaCy available')" && \
    python -m spacy download en_core_web_sm && \
    python -m spacy download de_core_news_sm || \
    echo "spaCy not available, skipping model downloads"

# Production stage
FROM base AS production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/{input,processed,state,vectors,reports,backups} logs && \
    if [ "${USER_ID}" != "0" ]; then \
        chown -R ${USER_ID}:${GROUP_ID} data logs; \
    fi

# Make scripts executable
RUN chmod +x run_pipeline.py test_pipeline.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python test_pipeline.py || exit 1

# Switch to non-root user (only if not root)
USER ${USER_ID}:${GROUP_ID}

# Expose port for potential web interface
EXPOSE 8000

# Default command
CMD ["python", "run_pipeline.py", "--help"]

# Development stage
FROM base AS development

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
COPY . .

# Create directories
RUN mkdir -p data/{input,processed,state,vectors,reports,backups} logs && \
    if [ "${USER_ID}" != "0" ]; then \
        chown -R ${USER_ID}:${GROUP_ID} data logs; \
    fi

# Make scripts executable
RUN chmod +x run_pipeline.py test_pipeline.py

USER ${USER_ID}:${GROUP_ID}

CMD ["bash"]