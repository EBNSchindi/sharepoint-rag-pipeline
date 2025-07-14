# ⚙️ Configuration Guide - SharePoint RAG Pipeline

**Umfassende Konfigurationsreferenz für optimale Performance**

## 🎯 Konfigurationsübersicht

Die Pipeline nutzt mehrere Konfigurationsebenen:

1. **Environment Variables** (.env) - Runtime-Einstellungen
2. **Pipeline Config** (config/pipeline.yaml) - Verarbeitungslogik
3. **Context Rules** (config/context_rules.yaml) - Kontext-Anreicherung
4. **Command Line Args** - Überschreibungen pro Ausführung
5. **Docker Environment** - Container-spezifische Einstellungen

---

## 🔧 Environment Variables (.env)

### Core Settings

```env
# ============================================================================
# CORE PIPELINE SETTINGS
# ============================================================================

# Input/Output Directories
INPUT_DIR=/path/to/sharepoint/pdfs          # Quell-PDF-Verzeichnis
OUTPUT_DIR=/app/data                        # Output-Verzeichnis (Container)
DATA_DIR=/app/data                          # Daten-Verzeichnis

# Processing Control
MAX_WORKERS=4                               # Anzahl parallele Worker (1-16)
MIN_QUALITY_SCORE=70                        # Qualitätsschwelle (0-100)
TIMEOUT_PER_DOCUMENT=300                    # Timeout pro Dokument (Sekunden)

# Memory Management
MAX_MEMORY_MB=4096                          # Max. RAM pro Worker (MB)
CHUNK_BATCH_SIZE=100                        # Chunks pro Batch
ENABLE_MEMORY_MONITORING=true              # Memory-Überwachung

# Processing Modes
FORCE_REPROCESS=false                       # Alle Dokumente neu verarbeiten
DRY_RUN=false                              # Nur Simulation
SKIP_EXISTING=true                         # Bereits verarbeitete überspringen
INCREMENTAL_MODE=true                      # Nur geänderte Dateien

# ============================================================================
# LOGGING & MONITORING
# ============================================================================

# Logging Configuration
LOG_LEVEL=INFO                             # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE=true                          # In Datei loggen
LOG_TO_CONSOLE=true                       # Auf Konsole ausgeben
LOG_FORMAT=structured                     # structured, simple, json
LOG_MAX_SIZE_MB=100                       # Max. Log-Dateigröße
LOG_BACKUP_COUNT=5                        # Anzahl Log-Backups

# Monitoring
ENABLE_METRICS=true                       # Performance-Metriken sammeln
METRICS_EXPORT_INTERVAL=60               # Metriken-Export (Sekunden)
HEALTH_CHECK_ENABLED=true                # Health-Check Endpoint

# ============================================================================
# STORAGE SETTINGS
# ============================================================================

# Vector Database
VECTOR_STORE_TYPE=chromadb                # chromadb, json_fallback, both
CHROMADB_HOST=localhost                   # ChromaDB Server
CHROMADB_PORT=8000                        # ChromaDB Port
CHROMADB_COLLECTION_PREFIX=sharepoint     # Collection-Präfix
USE_JSON_FALLBACK=true                    # JSON-Fallback aktivieren

# Metadata Database
METADATA_DB_TYPE=sqlite                   # sqlite, postgresql
SQLITE_DB_PATH=data/metadata/metadata.db  # SQLite-Pfad
POSTGRESQL_URL=postgresql://user:pass@host:port/db  # PostgreSQL Connection

# File Storage
BACKUP_ENABLED=true                       # Automatische Backups
BACKUP_INTERVAL_HOURS=24                  # Backup-Intervall
CLEANUP_OLD_BACKUPS=true                  # Alte Backups löschen
BACKUP_RETENTION_DAYS=30                  # Backup-Aufbewahrung

# ============================================================================
# PDF PROCESSING
# ============================================================================

# PDF Extraction
PDF_BACKEND_PRIORITY=pymupdf,pdfplumber,pypdf2,ocr  # Backend-Reihenfolge
ENABLE_OCR=true                           # OCR für gescannte PDFs
OCR_LANGUAGE=deu+eng                      # Tesseract-Sprachen
OCR_QUALITY=high                          # low, medium, high
PDF_PASSWORD_LIST=password1,password2     # Standard-Passwörter

# Text Processing
PRESERVE_FORMATTING=true                  # Layout-Erhaltung
EXTRACT_IMAGES=false                      # Bilder extrahieren
EXTRACT_TABLES=true                       # Tabellen extrahieren
NORMALIZE_TEXT=true                       # Text normalisieren

# ============================================================================
# CHUNKING & CONTEXT
# ============================================================================

# Chunking Strategy
CHUNK_SIZE=1000                           # Token pro Chunk
CHUNK_OVERLAP=200                         # Überlappung zwischen Chunks
CHUNKING_STRATEGY=contextual              # contextual, semantic, fixed
MIN_CHUNK_SIZE=100                        # Minimale Chunk-Größe
MAX_CHUNK_SIZE=2000                       # Maximale Chunk-Größe

# Context Enrichment
ENABLE_HIERARCHICAL_CONTEXT=true         # Hierarchie-Kontext
ENABLE_SEMANTIC_ROLES=true               # Semantische Rollen
ENABLE_CONCEPT_EXTRACTION=true           # Konzept-Extraktion
ENABLE_ENTITY_RECOGNITION=true           # Named Entity Recognition
CONTEXT_DEPTH_LEVELS=5                   # Max. Hierarchie-Tiefe

# ============================================================================
# AI & NLP SETTINGS
# ============================================================================

# Language Models
NLP_BACKEND=spacy                         # spacy, transformers, both
SPACY_MODEL=en_core_web_sm               # spaCy-Modell
TRANSFORMERS_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Embedding-Modell
ENABLE_GPU=false                          # GPU-Beschleunigung

# OpenAI Integration (Optional)
OPENAI_API_KEY=                           # OpenAI API Key (optional)
OPENAI_MODEL=gpt-3.5-turbo               # GPT-Modell
OPENAI_MAX_TOKENS=2000                    # Max. Token pro Request
ENABLE_AI_ENRICHMENT=false               # AI-basierte Anreicherung

# ============================================================================
# QUALITY CONTROL
# ============================================================================

# Quality Validation
ENABLE_QUALITY_VALIDATION=true           # Qualitätsprüfung aktivieren
QUALITY_CHECKS=completeness,coherence,density,context,language,technical,semantic
QUALITY_THRESHOLD_STRICT=90              # Strenge Qualitätsschwelle
QUALITY_THRESHOLD_RELAXED=60             # Lockere Qualitätsschwelle
REJECT_LOW_QUALITY=false                 # Niedrige Qualität ablehnen

# Error Handling
MAX_RETRIES=3                            # Max. Wiederholungsversuche
RETRY_DELAY_SECONDS=5                    # Verzögerung zwischen Versuchen
CONTINUE_ON_ERROR=true                   # Bei Fehlern fortfahren
ERROR_THRESHOLD_PERCENTAGE=20            # Max. Fehlerrate (%)

# ============================================================================
# SCHEDULING & AUTOMATION
# ============================================================================

# Cron Scheduling
CRON_SCHEDULE=0 2 1 * *                  # Cron-Ausdruck (monatlich um 2:00)
ENABLE_SCHEDULER=false                   # Scheduler aktivieren
TIMEZONE=Europe/Berlin                   # Zeitzone für Scheduler

# Automation Features
AUTO_CLEANUP_ENABLED=true                # Automatisches Aufräumen
CLEANUP_ORPHANED_DATA=true              # Verwaiste Daten löschen
AUTO_OPTIMIZE_STORAGE=true              # Storage-Optimierung
SEND_COMPLETION_EMAILS=false            # E-Mail-Benachrichtigungen

# ============================================================================
# SECURITY & PRIVACY
# ============================================================================

# Security Settings
ENABLE_INPUT_VALIDATION=true             # Input-Validierung
SANITIZE_OUTPUT=true                     # Output-Bereinigung
RESTRICT_FILE_ACCESS=true               # Dateizugriff beschränken
ANONYMOUS_MODE=false                     # Anonymer Modus

# Privacy Settings
STRIP_PERSONAL_DATA=false               # Persönliche Daten entfernen
REDACT_SENSITIVE_INFO=false             # Sensible Informationen schwärzen
ENABLE_AUDIT_LOG=true                   # Audit-Protokoll

# ============================================================================
# DEVELOPMENT & DEBUGGING
# ============================================================================

# Development Mode
DEVELOPMENT_MODE=false                   # Entwicklungsmodus
DEBUG_AGENTS=false                      # Agent-Debugging
PROFILING_ENABLED=false                 # Performance-Profiling
MEMORY_PROFILING=false                  # Memory-Profiling

# Testing
TEST_MODE=false                         # Test-Modus
SAMPLE_SIZE_LIMIT=0                     # Begrenzung für Tests (0=unbegrenzt)
MOCK_EXTERNAL_SERVICES=false           # Externe Services mocken
```

---

## 📝 Pipeline Configuration (config/pipeline.yaml)

### Complete Configuration Reference

```yaml
# ============================================================================
# PIPELINE CONFIGURATION
# ============================================================================

# Global Pipeline Settings
pipeline:
  name: "sharepoint-rag-pipeline"
  version: "2.0.0"
  description: "Contextual RAG Pipeline for SharePoint Knowledge Base"
  
  # Processing Control
  processing:
    max_workers: 4                      # Anzahl parallele Worker
    timeout_per_document: 300           # Timeout pro Dokument (Sekunden)
    batch_size: 10                      # Dokumente pro Batch
    max_memory_per_worker_mb: 1024      # Max. RAM pro Worker
    
    # Error Handling
    max_retries: 3
    retry_delay_seconds: 5
    continue_on_error: true
    error_threshold_percentage: 20
    
    # Progress Tracking
    progress_reporting_interval: 10     # Fortschritt alle N Dokumente
    save_state_interval: 100           # State alle N Dokumente speichern

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

agents:
  # PDF Extractor Agent
  pdf_extractor:
    enabled: true
    priority: 1
    
    # Backend Configuration
    backends:
      - name: "pymupdf"
        enabled: true
        priority: 1
        config:
          preserve_layout: true
          extract_images: false
          extract_tables: true
          
      - name: "pdfplumber"
        enabled: true
        priority: 2
        config:
          precision: high
          extract_tables: true
          table_settings:
            snap_tolerance: 3
            join_tolerance: 3
            
      - name: "pypdf2"
        enabled: true
        priority: 3
        config:
          strict: false
          
      - name: "ocr"
        enabled: true
        priority: 4
        config:
          language: "deu+eng"
          engine: "tesseract"
          dpi: 300
          image_preprocessing: true
    
    # Processing Options
    options:
      normalize_text: true
      remove_headers_footers: true
      merge_broken_lines: true
      handle_encrypted_pdfs: true
      password_attempts:
        - ""
        - "password"
        - "123456"
        - "admin"

  # Metadata Extractor Agent
  metadata_extractor:
    enabled: true
    priority: 2
    
    # Extraction Sources
    sources:
      file_system: true                 # Dateisystem-Metadaten
      pdf_metadata: true                # PDF-interne Metadaten
      content_analysis: true            # Content-basierte Analyse
      
    # Content Analysis
    content_analysis:
      language_detection: true
      document_type_classification: true
      topic_modeling: false
      sentiment_analysis: false
      
    # Language Detection
    language_detection:
      enabled: true
      confidence_threshold: 0.8
      fallback_language: "de"
      supported_languages: ["de", "en", "fr", "es"]

  # Chunk Creator Agent
  chunk_creator:
    enabled: true
    priority: 3
    
    # Chunking Strategy
    strategy: "contextual"              # contextual, semantic, fixed, adaptive
    
    # Size Configuration
    chunk_size: 1000                    # Target token count
    chunk_overlap: 200                  # Overlap between chunks
    min_chunk_size: 100                 # Minimum chunk size
    max_chunk_size: 2000                # Maximum chunk size
    
    # Contextual Chunking
    contextual_chunking:
      respect_paragraphs: true
      respect_sections: true
      respect_lists: true
      respect_tables: true
      semantic_boundaries:
        - "\\n\\n"                      # Paragraph breaks
        - "\\n# "                       # Headers
        - "\\n## "                      # Sub-headers
        - "\\n### "                     # Sub-sub-headers
        - "\\n\\d+\\."                  # Numbered lists
        - "\\n- "                       # Bullet points
        - "\\n\\* "                     # Asterisk lists
        
    # Token Counting
    tokenization:
      method: "tiktoken"                # tiktoken, spacy, simple
      model: "cl100k_base"             # For tiktoken
      
    # Quality Control
    quality_control:
      min_information_density: 0.3     # Minimum content/whitespace ratio
      max_repetition_ratio: 0.5        # Maximum repeated content ratio
      require_complete_sentences: true

  # Context Enricher Agent
  context_enricher:
    enabled: true
    priority: 4
    
    # Context Types
    context_types:
      document_context: true
      hierarchical_context: true
      navigational_context: true
      content_context: true
      
    # Document Context
    document_context:
      extract_title: true
      extract_authors: true
      extract_creation_date: true
      extract_document_type: true
      detect_language: true
      
    # Hierarchical Context
    hierarchical_context:
      max_depth_levels: 5
      header_patterns:
        - "^#+\\s+"                     # Markdown headers
        - "^\\d+\\.\\s+"               # Numbered sections
        - "^[IVX]+\\.\\s+"             # Roman numerals
        - "^[A-Z]\\.\\s+"              # Lettered sections
      section_detection:
        enabled: true
        confidence_threshold: 0.7
        
    # Navigational Context
    navigational_context:
      link_previous_next: true
      identify_related_chunks: true
      cross_reference_detection: true
      page_number_tracking: true
      
    # Content Context
    content_context:
      semantic_role_classification: true
      concept_extraction: true
      entity_recognition: true
      keyword_extraction: true
      summarization: false
      
    # NLP Configuration
    nlp:
      backend: "spacy"                  # spacy, transformers, openai
      spacy_model: "en_core_web_sm"
      batch_size: 100
      
    # Concept Extraction
    concept_extraction:
      method: "tfidf"                   # tfidf, textrank, yake
      max_concepts: 10
      min_concept_score: 0.1
      
    # Entity Recognition
    entity_recognition:
      enabled: true
      entity_types: ["PERSON", "ORG", "GPE", "DATE", "MONEY"]
      confidence_threshold: 0.8

  # Quality Validator Agent
  quality_validator:
    enabled: true
    priority: 5
    
    # Quality Checks
    checks:
      completeness:
        enabled: true
        weight: 1.0
        min_text_length: 50
        max_empty_ratio: 0.1
        
      coherence:
        enabled: true
        weight: 1.0
        sentence_connectivity: true
        topic_consistency: true
        
      information_density:
        enabled: true
        weight: 1.0
        min_density: 0.3
        max_repetition: 0.5
        
      context_richness:
        enabled: true
        weight: 1.0
        required_context_types: 3
        min_metadata_completeness: 0.7
        
      language_quality:
        enabled: true
        weight: 1.0
        spell_check: false
        grammar_check: false
        readability_check: true
        
      technical_accuracy:
        enabled: true
        weight: 1.0
        format_validation: true
        encoding_check: true
        
      semantic_consistency:
        enabled: true
        weight: 1.0
        topic_coherence: true
        concept_consistency: true
    
    # Scoring
    scoring:
      method: "weighted_average"        # weighted_average, minimum, maximum
      min_passing_score: 70
      strict_mode: false
      
    # Actions
    actions:
      reject_low_quality: false
      flag_for_review: true
      auto_retry: true
      max_retry_attempts: 2

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

storage:
  # Vector Store
  vector_store:
    primary_backend: "chromadb"         # chromadb, faiss, pinecone
    fallback_backend: "json"
    
    # ChromaDB Configuration
    chromadb:
      host: "localhost"
      port: 8000
      collection_prefix: "sharepoint"
      embedding_function: "sentence-transformers"
      embedding_model: "all-MiniLM-L6-v2"
      distance_metric: "cosine"
      
      # Performance
      batch_size: 100
      max_connections: 10
      connection_timeout: 30
      
    # JSON Fallback
    json_fallback:
      storage_path: "data/vectors/fallback"
      compression: true
      index_method: "linear"           # linear, annoy, faiss
      
  # Metadata Store
  metadata_store:
    backend: "sqlite"                   # sqlite, postgresql, mongodb
    
    # SQLite Configuration
    sqlite:
      database_path: "data/metadata/metadata.db"
      enable_wal: true
      cache_size: 1000
      synchronous: "NORMAL"
      journal_mode: "WAL"
      
    # Connection Pooling
    connection_pool:
      max_connections: 10
      timeout: 30
      retry_attempts: 3
      
  # File State Management
  state_management:
    backend: "json"                     # json, sqlite, redis
    storage_path: "data/state"
    backup_enabled: true
    compression: true

# ============================================================================
# MONITORING & LOGGING
# ============================================================================

monitoring:
  # Metrics Collection
  metrics:
    enabled: true
    collection_interval: 60            # Seconds
    export_format: "prometheus"        # prometheus, json, csv
    
    # Metric Types
    collect_processing_metrics: true
    collect_quality_metrics: true
    collect_performance_metrics: true
    collect_error_metrics: true
    
  # Health Checks
  health_checks:
    enabled: true
    endpoint_port: 8080
    check_interval: 30                  # Seconds
    
    # Check Types
    storage_health: true
    agent_health: true
    memory_health: true
    disk_health: true
    
  # Alerting
  alerting:
    enabled: false
    channels: ["email", "slack"]       # email, slack, webhook
    
    # Alert Conditions
    error_rate_threshold: 0.1          # 10% error rate
    memory_usage_threshold: 0.9        # 90% memory usage
    disk_usage_threshold: 0.9          # 90% disk usage
    processing_time_threshold: 3600    # 1 hour per document

logging:
  # Log Configuration
  level: "INFO"                         # DEBUG, INFO, WARNING, ERROR
  format: "structured"                  # structured, simple, json
  
  # Output Destinations
  console:
    enabled: true
    level: "INFO"
    format: "simple"
    
  file:
    enabled: true
    level: "DEBUG"
    format: "structured"
    path: "logs/contextual_pipeline.log"
    max_size_mb: 100
    backup_count: 5
    rotation: "size"                    # size, time
    
  # Structured Logging
  structured:
    include_timestamp: true
    include_level: true
    include_logger_name: true
    include_thread_id: true
    include_process_id: true
    
  # Log Sampling
  sampling:
    enabled: false
    sample_rate: 0.1                    # Log 10% of debug messages
    
# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

performance:
  # Memory Management
  memory:
    max_total_memory_gb: 8
    max_memory_per_worker_gb: 2
    enable_memory_monitoring: true
    gc_collection_threshold: 0.8       # Trigger GC at 80% memory usage
    
  # CPU Optimization
  cpu:
    enable_multiprocessing: true
    cpu_affinity: []                    # Empty = use all CPUs
    nice_level: 0                       # Process priority
    
  # I/O Optimization
  io:
    read_buffer_size: 8192             # Bytes
    write_buffer_size: 8192            # Bytes
    enable_async_io: false
    
  # Caching
  caching:
    enable_result_caching: true
    cache_size_mb: 256
    cache_ttl_seconds: 3600
    
    # Cache Types
    pdf_extraction_cache: true
    metadata_cache: true
    embedding_cache: true

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

security:
  # Input Validation
  input_validation:
    enabled: true
    max_file_size_mb: 100
    allowed_file_types: [".pdf"]
    scan_for_malware: false
    
    # Path Security
    prevent_path_traversal: true
    allowed_input_paths: []             # Empty = no restrictions
    
  # Output Sanitization
  output_sanitization:
    enabled: true
    remove_metadata: false
    anonymize_personal_data: false
    redact_sensitive_patterns: []
    
  # Access Control
  access_control:
    require_authentication: false
    api_key_required: false
    ip_whitelist: []                    # Empty = allow all
    
  # Audit Logging
  audit:
    enabled: true
    log_level: "INFO"
    include_content_hashes: true
    include_processing_metadata: true
```

---

## 🧩 Context Rules Configuration (config/context_rules.yaml)

```yaml
# ============================================================================
# CONTEXT ENRICHMENT RULES
# ============================================================================

# Document Type Classification Rules
document_types:
  manual:
    patterns:
      - "user.*manual"
      - "handbuch"
      - "bedienungsanleitung"
    context_boost: 1.2
    
  policy:
    patterns:
      - "policy"
      - "richtlinie"
      - "verfahrensanweisung"
    context_boost: 1.1
    
  technical:
    patterns:
      - "technical.*specification"
      - "technische.*dokumentation"
      - "API.*documentation"
    context_boost: 1.3

# Hierarchical Structure Rules
hierarchy_patterns:
  chapters:
    - "^(Kapitel|Chapter)\\s+\\d+"
    - "^\\d+\\.\\s+[A-ZÄÖÜ]"
    
  sections:
    - "^\\d+\\.\\d+\\s+"
    - "^[A-Z]\\.\\s+[A-ZÄÖÜ]"
    
  subsections:
    - "^\\d+\\.\\d+\\.\\d+\\s+"
    - "^[a-z]\\)\\s+"

# Semantic Role Classification
semantic_roles:
  introduction:
    patterns:
      - "^(Einleitung|Introduction|Überblick)"
      - "^(Zusammenfassung|Summary|Executive Summary)"
    weight: 1.0
    
  main_content:
    patterns:
      - "^(Hauptteil|Main Content|Details)"
      - "^(Beschreibung|Description)"
    weight: 1.2
    
  examples:
    patterns:
      - "^(Beispiel|Example|Demonstration)"
      - "^(Anwendungsfall|Use Case)"
    weight: 1.1
    
  troubleshooting:
    patterns:
      - "^(Fehlerbehebung|Troubleshooting|Problem)"
      - "^(FAQ|Häufige Fragen)"
    weight: 1.3

# Concept Extraction Rules
concept_extraction:
  technical_terms:
    patterns:
      - "[A-Z]{2,}(?:[A-Z][a-z]+)+"     # CamelCase
      - "[A-Z]+(?:_[A-Z]+)+"           # UPPER_CASE
    boost: 1.2
    
  domain_specific:
    sharepoint:
      - "SharePoint"
      - "SPO"
      - "OneDrive"
      - "Teams"
    boost: 1.5
    
  processes:
    patterns:
      - "\\b\\w+(?:ing|ung|tion|sion)\\b"
    boost: 1.1

# Navigation Context Rules
navigation:
  cross_references:
    patterns:
      - "siehe (Kapitel|Abschnitt|Seite)\\s*\\d+"
      - "see (chapter|section|page)\\s*\\d+"
      - "vgl\\.|cf\\.|compare"
    
  related_content:
    similarity_threshold: 0.8
    max_related_chunks: 5
    
  sequence_indicators:
    - "zuerst|first|initially"
    - "dann|then|next"
    - "schließlich|finally|lastly"
```

---

## 🚀 Performance Tuning Guide

### Memory Optimization

```env
# Für Systeme mit 4GB RAM
MAX_WORKERS=2
MAX_MEMORY_MB=1024
CHUNK_BATCH_SIZE=50

# Für Systeme mit 8GB RAM
MAX_WORKERS=4
MAX_MEMORY_MB=2048
CHUNK_BATCH_SIZE=100

# Für Systeme mit 16GB+ RAM
MAX_WORKERS=8
MAX_MEMORY_MB=4096
CHUNK_BATCH_SIZE=200
```

### CPU Optimization

```yaml
# pipeline.yaml
performance:
  cpu:
    enable_multiprocessing: true
    nice_level: 0                       # Normal priority
    
processing:
  max_workers: 8                        # = CPU cores
  batch_size: 20                        # Higher for CPU-intensive tasks
```

### Storage Optimization

```env
# SSD Storage
ENABLE_RESULT_CACHING=true
CACHE_SIZE_MB=512

# Network Storage
CACHE_SIZE_MB=256
READ_BUFFER_SIZE=16384
```

---

## 🔧 Environment-Specific Configurations

### Development Environment

```env
# .env.development
DEVELOPMENT_MODE=true
LOG_LEVEL=DEBUG
DEBUG_AGENTS=true
PROFILING_ENABLED=true
TEST_MODE=true
SAMPLE_SIZE_LIMIT=10
MAX_WORKERS=2
```

### Staging Environment

```env
# .env.staging  
LOG_LEVEL=INFO
ENABLE_METRICS=true
MAX_WORKERS=4
BACKUP_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### Production Environment

```env
# .env.production
LOG_LEVEL=WARNING
ENABLE_METRICS=true
ENABLE_AUDIT_LOG=true
MAX_WORKERS=8
BACKUP_ENABLED=true
AUTO_CLEANUP_ENABLED=true
SEND_COMPLETION_EMAILS=true
```

---

## 🏢 Enterprise Configuration

### High-Volume Processing

```yaml
# pipeline.yaml for enterprise
processing:
  max_workers: 16
  batch_size: 50
  timeout_per_document: 600

performance:
  memory:
    max_total_memory_gb: 32
    max_memory_per_worker_gb: 2
    
  caching:
    cache_size_mb: 2048
    enable_result_caching: true

storage:
  vector_store:
    chromadb:
      batch_size: 500
      max_connections: 20
```

### Multi-Language Support

```env
# Mehrsprachige Dokumente
OCR_LANGUAGE=deu+eng+fra+spa
NLP_MODELS=de_core_news_sm,en_core_web_sm,fr_core_news_sm
SUPPORTED_LANGUAGES=de,en,fr,es
```

### Security-Hardened Configuration

```yaml
security:
  input_validation:
    enabled: true
    scan_for_malware: true
    max_file_size_mb: 50
    
  output_sanitization:
    enabled: true
    anonymize_personal_data: true
    remove_metadata: true
    
  access_control:
    require_authentication: true
    ip_whitelist: ["10.0.0.0/8", "192.168.0.0/16"]
    
  audit:
    enabled: true
    include_content_hashes: true
```

---

## 📊 Configuration Validation

### Validation Script

```bash
#!/bin/bash
# validate_config.sh

echo "🔍 Validating Pipeline Configuration..."

# Check environment file
if [ ! -f .env ]; then
    echo "❌ .env file missing"
    exit 1
fi

# Check required variables
required_vars=("INPUT_DIR" "MAX_WORKERS" "MIN_QUALITY_SCORE")
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" .env; then
        echo "❌ Missing required variable: $var"
        exit 1
    fi
done

# Validate numeric values
max_workers=$(grep "^MAX_WORKERS=" .env | cut -d'=' -f2)
if ! [[ "$max_workers" =~ ^[0-9]+$ ]] || [ "$max_workers" -lt 1 ] || [ "$max_workers" -gt 32 ]; then
    echo "❌ MAX_WORKERS must be between 1 and 32"
    exit 1
fi

# Check configuration files
if [ ! -f config/pipeline.yaml ]; then
    echo "❌ pipeline.yaml missing"
    exit 1
fi

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/pipeline.yaml'))" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Invalid YAML syntax in pipeline.yaml"
    exit 1
fi

echo "✅ Configuration validation passed"
```

### Docker Configuration Check

```bash
# Config-Check in Container
make config-check

# Oder manuell:
docker run --rm -v "$(pwd):/app" sharepoint-rag-pipeline:latest \
  python -c "
from src.pipeline.config import ConfigManager
config = ConfigManager()
print('✅ Configuration loaded successfully')
print(f'Workers: {config.get(\"processing.max_workers\")}')
print(f'Quality: {config.get(\"quality_validation.min_quality_score\")}')
"
```

---

## 🎛️ Runtime Configuration Override

### Command Line Overrides

```bash
# Temporäre Überschreibungen
python run_pipeline.py /path/to/pdfs \
  --workers 2 \
  --quality-score 80 \
  --timeout 600 \
  --config custom_config.yaml

# Docker Overrides
docker run -e MAX_WORKERS=8 -e MIN_QUALITY_SCORE=90 \
  sharepoint-rag-pipeline:latest
```

### Dynamic Configuration Updates

```python
# Zur Laufzeit konfigurieren
from src.pipeline.config import ConfigManager

config = ConfigManager()
config.update({
    'processing.max_workers': 6,
    'quality_validation.min_quality_score': 85
})
config.save()
```

Diese umfassende Konfigurationsreferenz ermöglicht es, die Pipeline optimal an spezifische Anforderungen und Umgebungen anzupassen.