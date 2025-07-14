# 🔧 API Reference - SharePoint RAG Pipeline

**Vollständige Entwickler-Referenz für Integration und Erweiterung**

## 🎯 Overview

Die SharePoint RAG Pipeline bietet verschiedene APIs für:
- **Programmatische Nutzung** der Pipeline
- **Erweiterung** mit eigenen Agenten
- **Integration** in bestehende Systeme
- **Monitoring** und **Steuerung**

---

## 📚 Core API Components

### 1. Pipeline Orchestrator API

#### Grundlegende Verwendung

```python
from src.pipeline.orchestrator import ContextualRAGOrchestrator
from src.pipeline.config import ConfigManager
from pathlib import Path

# Pipeline initialisieren
config = ConfigManager("config/pipeline.yaml")
orchestrator = ContextualRAGOrchestrator(config)

# Dokumente verarbeiten
input_path = Path("/path/to/pdfs")
results = orchestrator.process_documents(
    input_path=input_path,
    force_reprocess=False,
    dry_run=False
)

# Ergebnisse auswerten
print(f"Verarbeitete Dokumente: {results.total_processed}")
print(f"Erfolgreich: {results.successful}")
print(f"Fehler: {results.failed}")
print(f"Chunks erstellt: {results.total_chunks}")
```

#### Erweiterte Konfiguration

```python
# Custom Configuration
custom_config = {
    "processing": {
        "max_workers": 8,
        "timeout_per_document": 600
    },
    "quality_validation": {
        "min_quality_score": 85
    }
}

orchestrator = ContextualRAGOrchestrator(custom_config)

# Mit Callbacks
def progress_callback(processed: int, total: int, current_file: str):
    print(f"Progress: {processed}/{total} - Current: {current_file}")

def error_callback(error: Exception, file_path: str):
    print(f"Error processing {file_path}: {error}")

results = orchestrator.process_documents(
    input_path=input_path,
    progress_callback=progress_callback,
    error_callback=error_callback
)
```

#### Batch Processing API

```python
# Mehrere Verzeichnisse parallel verarbeiten
batch_results = orchestrator.process_batch([
    {"path": "/path/to/pdfs1", "config_override": {"max_workers": 4}},
    {"path": "/path/to/pdfs2", "config_override": {"max_workers": 2}},
    {"path": "/path/to/pdfs3", "config_override": {"quality_threshold": 90}}
])

for result in batch_results:
    print(f"Path: {result.input_path}")
    print(f"Status: {result.status}")
    print(f"Chunks: {result.chunk_count}")
```

---

### 2. Agent Development API

#### Base Agent Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.models.contextual_chunk import ContextualChunk
from src.models.processing_context import ProcessingContext

class BaseAgent(ABC):
    """Basis-Interface für alle Pipeline-Agenten"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.enabled = config.get("enabled", True)
        
    @abstractmethod
    def process(self, context: ProcessingContext) -> AgentResult:
        """Hauptverarbeitungslogik des Agenten"""
        pass
        
    def validate_input(self, context: ProcessingContext) -> bool:
        """Input-Validierung"""
        return True
        
    def on_error(self, error: Exception, context: ProcessingContext) -> None:
        """Fehlerbehandlung"""
        print(f"Error in {self.name}: {error}")
        
    def get_metrics(self) -> Dict[str, Any]:
        """Agent-spezifische Metriken"""
        return {}
```

#### Custom Agent Beispiel

```python
from src.agents.base_agent import BaseAgent
from src.models.agent_result import AgentResult
import re

class CustomDocumentClassifierAgent(BaseAgent):
    """Beispiel: Custom Document Classifier"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.classification_rules = config.get("classification_rules", {})
        self.confidence_threshold = config.get("confidence_threshold", 0.8)
        
    def process(self, context: ProcessingContext) -> AgentResult:
        """Klassifiziert Dokumente basierend auf Content-Patterns"""
        
        document_text = context.document.content
        classification_scores = {}
        
        # Regelbasierte Klassifikation
        for doc_type, patterns in self.classification_rules.items():
            score = self._calculate_pattern_score(document_text, patterns)
            classification_scores[doc_type] = score
            
        # Beste Klassifikation ermitteln
        best_type = max(classification_scores, key=classification_scores.get)
        confidence = classification_scores[best_type]
        
        # Metadaten aktualisieren
        if confidence >= self.confidence_threshold:
            context.document.metadata["document_type"] = best_type
            context.document.metadata["classification_confidence"] = confidence
            
        return AgentResult(
            success=True,
            data={
                "document_type": best_type,
                "confidence": confidence,
                "all_scores": classification_scores
            },
            metrics={
                "classification_time": 0.1,
                "confidence_score": confidence
            }
        )
        
    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> float:
        """Berechnet Pattern-Matching Score"""
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        return matches / len(patterns) if patterns else 0.0

# Agent registrieren
orchestrator.register_agent("document_classifier", CustomDocumentClassifierAgent({
    "classification_rules": {
        "manual": ["benutzerhandbuch", "user manual", "anleitung"],
        "policy": ["richtlinie", "policy", "verfahren"],
        "technical": ["api", "technical", "specification"]
    },
    "confidence_threshold": 0.7
}))
```

#### Agent Pipeline Integration

```python
# Agent in Pipeline einbinden
orchestrator.add_processing_step(
    step_name="document_classification",
    agents=["document_classifier"],
    dependencies=["metadata_extraction"],  # Nach Metadaten-Extraktion
    optional=True  # Agent ist optional
)

# Agent-Konfiguration zur Laufzeit ändern
orchestrator.update_agent_config("document_classifier", {
    "confidence_threshold": 0.8
})

# Agent deaktivieren/aktivieren
orchestrator.enable_agent("document_classifier")
orchestrator.disable_agent("document_classifier")
```

---

### 3. Storage API

#### Vector Store API

```python
from src.storage.vector_store import VectorStore
from src.models.contextual_chunk import ContextualChunk

# Vector Store initialisieren
vector_store = VectorStore(config={
    "backend": "chromadb",
    "fallback_backend": "json",
    "collection_name": "documents"
})

# Chunks speichern
chunks = [chunk1, chunk2, chunk3]  # ContextualChunk objects
success = vector_store.store_chunks(chunks)

# Ähnlichkeitssuche
query = "SharePoint configuration"
similar_chunks = vector_store.query_similar(
    query=query,
    limit=10,
    similarity_threshold=0.8,
    filters={
        "document_type": "manual",
        "quality_score": {"$gte": 70}
    }
)

# Ergebnisse verarbeiten
for result in similar_chunks:
    print(f"Chunk ID: {result.chunk_id}")
    print(f"Similarity: {result.similarity_score:.3f}")
    print(f"Content: {result.content[:100]}...")
```

#### Metadata Store API

```python
from src.storage.metadata_store import MetadataStore

metadata_store = MetadataStore(config={
    "backend": "sqlite",
    "database_path": "data/metadata/metadata.db"
})

# Dokument-Metadaten abrufen
document_metadata = metadata_store.get_document_metadata(document_id)

# Erweiterte Abfragen
search_results = metadata_store.search_documents(
    filters={
        "document_type": "manual",
        "language": "de",
        "creation_date": {"$gte": "2023-01-01"}
    },
    sort_by="quality_score",
    limit=50
)

# Aggregationen
stats = metadata_store.get_collection_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Average quality: {stats['average_quality_score']}")
print(f"Document types: {stats['document_type_distribution']}")
```

#### Custom Storage Backend

```python
from src.storage.interfaces import VectorStoreInterface
from typing import List, Dict, Any

class CustomVectorStore(VectorStoreInterface):
    """Custom Vector Store Implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = self._initialize_connection()
        
    def store_chunks(self, chunks: List[ContextualChunk]) -> bool:
        """Chunks in custom backend speichern"""
        try:
            for chunk in chunks:
                # Custom storage logic
                self._store_single_chunk(chunk)
            return True
        except Exception as e:
            print(f"Storage error: {e}")
            return False
            
    def query_similar(self, query: str, limit: int = 10, 
                     **kwargs) -> List[SimilarityResult]:
        """Ähnlichkeitssuche implementieren"""
        # Custom similarity search logic
        results = self._perform_similarity_search(query, limit)
        return results
        
    def _initialize_connection(self):
        """Custom connection setup"""
        pass
        
    def _store_single_chunk(self, chunk: ContextualChunk):
        """Einzelnen Chunk speichern"""
        pass
        
    def _perform_similarity_search(self, query: str, limit: int):
        """Similarity search logic"""
        pass

# Custom Backend registrieren
vector_store = VectorStore(config={
    "backend": "custom",
    "custom_backend_class": CustomVectorStore,
    "custom_config": {
        "connection_string": "custom://config"
    }
})
```

---

### 4. Query & Retrieval API

#### RAG Query Interface

```python
from src.retrieval.rag_query import RAGQueryEngine

# Query Engine initialisieren
query_engine = RAGQueryEngine(
    vector_store=vector_store,
    metadata_store=metadata_store,
    config={
        "max_results": 10,
        "similarity_threshold": 0.7,
        "context_window": 3  # Umgebende Chunks einbeziehen
    }
)

# Einfache Abfrage
results = query_engine.query(
    query="Wie konfiguriere ich SharePoint?",
    filters={
        "document_type": "manual",
        "language": "de"
    }
)

# Ergebnisse mit Context
for result in results:
    print(f"Document: {result.document_title}")
    print(f"Relevance: {result.relevance_score:.3f}")
    print(f"Context: {result.contextual_info}")
    print(f"Content: {result.content}")
    print("---")
```

#### Advanced Retrieval

```python
# Multi-Modal Retrieval
advanced_results = query_engine.advanced_query(
    query="SharePoint Berechtigungen",
    query_type="semantic",  # semantic, keyword, hybrid
    boost_factors={
        "recency": 1.2,      # Neuere Dokumente bevorzugen
        "quality": 1.5,      # Höhere Qualität bevorzugen
        "document_type": {   # Dokumenttyp-spezifische Gewichtung
            "manual": 1.3,
            "policy": 1.1
        }
    },
    expansion_config={
        "enable_query_expansion": True,
        "synonyms": ["Berechtigung", "Zugriff", "Permission", "Access"],
        "related_concepts": ["Security", "Authentication", "Authorization"]
    }
)

# Chunk-übergreifende Antworten
contextual_answer = query_engine.generate_contextual_answer(
    query="Wie setze ich SharePoint Berechtigungen?",
    max_chunks=5,
    include_sources=True,
    answer_style="detailed"  # detailed, concise, bullet_points
)
```

---

### 5. Monitoring & Metrics API

#### Performance Monitoring

```python
from src.monitoring.performance_monitor import PerformanceMonitor
from src.monitoring.metrics_collector import MetricsCollector

# Performance Monitor
monitor = PerformanceMonitor(config={
    "collection_interval": 60,  # Sekunden
    "metrics_retention_days": 30
})

# Metriken sammeln
metrics = monitor.collect_metrics()
print(f"Processing rate: {metrics['docs_per_minute']}")
print(f"Memory usage: {metrics['memory_usage_mb']} MB")
print(f"Quality distribution: {metrics['quality_distribution']}")

# Custom Metriken hinzufügen
monitor.add_custom_metric("custom_processing_time", 1.23)
monitor.add_custom_metric("custom_accuracy", 0.95)

# Alerts konfigurieren
monitor.add_alert(
    name="high_error_rate",
    condition="error_rate > 0.1",  # 10% Fehlerrate
    action="send_email",
    recipients=["admin@company.com"]
)
```

#### Health Check API

```python
from src.monitoring.health_checker import HealthChecker

health_checker = HealthChecker()

# System Health prüfen
health_status = health_checker.check_system_health()
print(f"Overall status: {health_status.overall_status}")

for component, status in health_status.components.items():
    print(f"{component}: {status.status} - {status.message}")

# Individual Component Checks
storage_health = health_checker.check_storage_health()
agent_health = health_checker.check_agents_health()
memory_health = health_checker.check_memory_health()

# Custom Health Checks
def custom_health_check():
    """Custom health check logic"""
    try:
        # Custom validation logic
        return HealthCheckResult(
            status="healthy",
            message="Custom check passed",
            details={"custom_metric": 42}
        )
    except Exception as e:
        return HealthCheckResult(
            status="unhealthy",
            message=f"Custom check failed: {e}",
            details={}
        )

health_checker.register_check("custom_check", custom_health_check)
```

---

### 6. Configuration API

#### Dynamic Configuration

```python
from src.pipeline.config import ConfigManager

config_manager = ConfigManager("config/pipeline.yaml")

# Aktuelle Konfiguration abrufen
current_config = config_manager.get_config()
max_workers = config_manager.get("processing.max_workers")

# Konfiguration zur Laufzeit ändern
config_manager.update({
    "processing.max_workers": 8,
    "quality_validation.min_quality_score": 85
})

# Änderungen speichern
config_manager.save()

# Konfiguration validieren
validation_result = config_manager.validate()
if not validation_result.is_valid:
    print(f"Config errors: {validation_result.errors}")

# Environment-spezifische Configs
dev_config = config_manager.load_environment_config("development")
prod_config = config_manager.load_environment_config("production")
```

#### Configuration Templates

```python
# Vordefinierte Templates verwenden
templates = {
    "high_performance": {
        "processing.max_workers": 16,
        "performance.memory.max_total_memory_gb": 32,
        "storage.vector_store.chromadb.batch_size": 500
    },
    "memory_optimized": {
        "processing.max_workers": 2,
        "processing.batch_size": 5,
        "performance.memory.max_memory_per_worker_gb": 1
    },
    "quality_focused": {
        "quality_validation.min_quality_score": 90,
        "agents.quality_validator.checks.*.weight": 1.5
    }
}

# Template anwenden
config_manager.apply_template("high_performance")
```

---

### 7. Event System API

#### Event-Driven Processing

```python
from src.events.event_system import EventSystem, Event
from src.events.handlers import EventHandler

# Event System initialisieren
event_system = EventSystem()

# Custom Event Handler
class CustomEventHandler(EventHandler):
    def handle_document_processed(self, event: Event):
        """Wird ausgelöst, wenn ein Dokument verarbeitet wurde"""
        document_id = event.data["document_id"]
        chunk_count = event.data["chunk_count"]
        quality_score = event.data["average_quality_score"]
        
        print(f"Document {document_id} processed: {chunk_count} chunks, quality: {quality_score}")
        
        # Custom logic, z.B. Benachrichtigung senden
        if quality_score < 70:
            self.send_quality_alert(document_id, quality_score)
            
    def handle_processing_error(self, event: Event):
        """Wird bei Verarbeitungsfehlern ausgelöst"""
        error = event.data["error"]
        file_path = event.data["file_path"]
        
        # Error logging and handling
        self.log_error(error, file_path)
        
    def send_quality_alert(self, document_id: str, quality_score: float):
        """Custom alert logic"""
        pass
        
    def log_error(self, error: Exception, file_path: str):
        """Custom error logging"""
        pass

# Handler registrieren
handler = CustomEventHandler()
event_system.register_handler("document_processed", handler.handle_document_processed)
event_system.register_handler("processing_error", handler.handle_processing_error)

# Events manuell auslösen
event_system.emit_event("custom_event", {
    "message": "Custom event data",
    "timestamp": datetime.now()
})
```

---

### 8. Integration APIs

#### REST API Server

```python
from flask import Flask, jsonify, request
from src.api.rest_server import create_app

# REST API Server starten
app = create_app(orchestrator, config)

@app.route('/api/v1/process', methods=['POST'])
def process_documents():
    """API Endpoint für Dokumentverarbeitung"""
    data = request.json
    input_path = data.get('input_path')
    config_override = data.get('config', {})
    
    try:
        results = orchestrator.process_documents(
            input_path=input_path,
            config_override=config_override
        )
        
        return jsonify({
            "status": "success",
            "results": {
                "total_processed": results.total_processed,
                "successful": results.successful,
                "failed": results.failed,
                "total_chunks": results.total_chunks
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/query', methods=['POST'])
def query_documents():
    """API Endpoint für Dokumentabfragen"""
    data = request.json
    query = data.get('query')
    filters = data.get('filters', {})
    limit = data.get('limit', 10)
    
    results = query_engine.query(
        query=query,
        filters=filters,
        limit=limit
    )
    
    return jsonify({
        "status": "success",
        "results": [
            {
                "chunk_id": r.chunk_id,
                "content": r.content,
                "relevance_score": r.relevance_score,
                "document_title": r.document_title,
                "metadata": r.metadata
            }
            for r in results
        ]
    })

# Server starten
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
```

#### WebSocket API

```python
import asyncio
import websockets
import json
from src.api.websocket_server import WebSocketServer

class PipelineWebSocketServer(WebSocketServer):
    """WebSocket Server für Real-time Updates"""
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'process_request':
                    await self.handle_process_request(websocket, data)
                elif data['type'] == 'query_request':
                    await self.handle_query_request(websocket, data)
                elif data['type'] == 'status_request':
                    await self.handle_status_request(websocket)
                    
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
            
    async def handle_process_request(self, websocket, data):
        """Handle document processing request"""
        input_path = data['input_path']
        
        # Progress callback für WebSocket
        async def progress_callback(processed, total, current_file):
            await websocket.send(json.dumps({
                "type": "progress_update",
                "processed": processed,
                "total": total,
                "current_file": current_file
            }))
        
        # Processing starten
        results = await self.process_documents_async(
            input_path=input_path,
            progress_callback=progress_callback
        )
        
        # Ergebnis senden
        await websocket.send(json.dumps({
            "type": "process_complete",
            "results": results.to_dict()
        }))

# WebSocket Server starten
async def start_websocket_server():
    server = PipelineWebSocketServer(orchestrator)
    await websockets.serve(server.handle_client, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")

# Event Loop starten
asyncio.run(start_websocket_server())
```

---

### 9. Testing API

#### Unit Testing Framework

```python
import unittest
from src.testing.test_framework import PipelineTestCase
from src.testing.mock_data import MockDataGenerator

class CustomAgentTest(PipelineTestCase):
    """Test Suite für Custom Agents"""
    
    def setUp(self):
        super().setUp()
        self.mock_generator = MockDataGenerator()
        self.test_agent = CustomDocumentClassifierAgent(self.test_config)
        
    def test_document_classification(self):
        """Test document classification logic"""
        # Mock document erstellen
        mock_document = self.mock_generator.create_mock_document(
            content="This is a user manual for SharePoint configuration",
            metadata={"title": "SharePoint User Guide"}
        )
        
        # Processing context erstellen
        context = self.create_test_context(mock_document)
        
        # Agent ausführen
        result = self.test_agent.process(context)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.data["document_type"], "manual")
        self.assertGreater(result.data["confidence"], 0.7)
        
    def test_pattern_matching(self):
        """Test pattern matching accuracy"""
        test_cases = [
            ("user manual configuration", "manual"),
            ("company policy document", "policy"),
            ("API technical specification", "technical")
        ]
        
        for content, expected_type in test_cases:
            with self.subTest(content=content):
                mock_doc = self.mock_generator.create_mock_document(content=content)
                context = self.create_test_context(mock_doc)
                result = self.test_agent.process(context)
                
                self.assertEqual(result.data["document_type"], expected_type)

# Test Suite ausführen
if __name__ == '__main__':
    unittest.main()
```

#### Integration Testing

```python
from src.testing.integration_tests import IntegrationTestSuite

class PipelineIntegrationTest(IntegrationTestSuite):
    """Integration Tests für die gesamte Pipeline"""
    
    def test_end_to_end_processing(self):
        """Test complete pipeline processing"""
        # Test PDF erstellen
        test_pdf_path = self.create_test_pdf(
            content="Test document content for SharePoint RAG pipeline",
            title="Test Document"
        )
        
        # Pipeline ausführen
        results = self.orchestrator.process_documents(
            input_path=test_pdf_path.parent,
            config_override={"processing.max_workers": 1}
        )
        
        # Ergebnisse validieren
        self.assertEqual(results.total_processed, 1)
        self.assertEqual(results.successful, 1)
        self.assertGreater(results.total_chunks, 0)
        
        # Vector Store prüfen
        stored_chunks = self.vector_store.get_chunks_by_document(
            document_id=results.document_ids[0]
        )
        self.assertGreater(len(stored_chunks), 0)
        
        # Metadaten prüfen
        metadata = self.metadata_store.get_document_metadata(
            document_id=results.document_ids[0]
        )
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["title"], "Test Document")
        
    def test_query_functionality(self):
        """Test query and retrieval functionality"""
        # Documents für Query-Test verarbeiten
        self.setup_test_documents()
        
        # Query ausführen
        results = self.query_engine.query(
            query="SharePoint configuration",
            limit=5
        )
        
        # Ergebnisse validieren
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertGreater(result.relevance_score, 0.0)
            self.assertIsNotNone(result.content)
```

---

### 10. Deployment API

#### Container Management

```python
from src.deployment.container_manager import ContainerManager
import docker

class PipelineContainerManager(ContainerManager):
    """Container Management für Pipeline Deployment"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.container_name = "sharepoint-rag-pipeline"
        
    def deploy_pipeline(self, config: Dict[str, Any]) -> bool:
        """Deploy pipeline in container"""
        try:
            # Container konfiguration
            container_config = {
                "image": "sharepoint-rag-pipeline:latest",
                "name": self.container_name,
                "environment": self._prepare_environment(config),
                "volumes": self._prepare_volumes(config),
                "ports": {"8080/tcp": 8080}
            }
            
            # Container starten
            container = self.docker_client.containers.run(
                detach=True,
                **container_config
            )
            
            print(f"Pipeline deployed: {container.id}")
            return True
            
        except Exception as e:
            print(f"Deployment failed: {e}")
            return False
            
    def scale_pipeline(self, replicas: int) -> bool:
        """Scale pipeline horizontally"""
        try:
            for i in range(replicas):
                container_name = f"{self.container_name}-{i}"
                # Additional container logic
                
            return True
        except Exception as e:
            print(f"Scaling failed: {e}")
            return False
            
    def update_pipeline(self, new_image: str) -> bool:
        """Rolling update of pipeline"""
        try:
            # Rolling update logic
            old_container = self.docker_client.containers.get(self.container_name)
            
            # Start new container
            new_container = self.docker_client.containers.run(
                image=new_image,
                name=f"{self.container_name}-new",
                detach=True
            )
            
            # Health check on new container
            if self._health_check(new_container):
                # Stop old container
                old_container.stop()
                old_container.remove()
                
                # Rename new container
                new_container.rename(self.container_name)
                return True
            else:
                new_container.stop()
                new_container.remove()
                return False
                
        except Exception as e:
            print(f"Update failed: {e}")
            return False

# Deployment ausführen
container_manager = PipelineContainerManager()
success = container_manager.deploy_pipeline({
    "max_workers": 8,
    "input_dir": "/data/sharepoint/pdfs",
    "quality_threshold": 80
})
```

#### Kubernetes Integration

```python
from kubernetes import client, config
from src.deployment.k8s_manager import KubernetesManager

class PipelineK8sManager(KubernetesManager):
    """Kubernetes Deployment Management"""
    
    def __init__(self):
        config.load_incluster_config()  # or load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        
    def deploy_pipeline_cluster(self, replicas: int = 3) -> bool:
        """Deploy pipeline as Kubernetes deployment"""
        
        # Deployment manifest
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name="rag-pipeline"),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": "rag-pipeline"}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": "rag-pipeline"}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="rag-pipeline",
                                image="sharepoint-rag-pipeline:latest",
                                resources=client.V1ResourceRequirements(
                                    limits={"memory": "4Gi", "cpu": "2"},
                                    requests={"memory": "2Gi", "cpu": "1"}
                                ),
                                env=[
                                    client.V1EnvVar(name="MAX_WORKERS", value="4"),
                                    client.V1EnvVar(name="MIN_QUALITY_SCORE", value="70")
                                ]
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            self.apps_v1.create_namespaced_deployment(
                namespace="default",
                body=deployment
            )
            print(f"Deployment created with {replicas} replicas")
            return True
        except Exception as e:
            print(f"K8s deployment failed: {e}")
            return False
```

---

## 🔗 SDK Usage Examples

### Python SDK

```python
# Complete SDK example
from sharepoint_rag_pipeline import PipelineSDK

# SDK initialisieren
sdk = PipelineSDK(
    config_path="config/pipeline.yaml",
    api_key="optional-api-key"
)

# Dokumente verarbeiten
results = sdk.process_documents(
    input_path="/path/to/pdfs",
    config={
        "max_workers": 4,
        "quality_threshold": 80
    }
)

# Queries ausführen
query_results = sdk.query(
    query="SharePoint Berechtigungen konfigurieren",
    filters={"document_type": "manual"},
    limit=10
)

# Monitoring
status = sdk.get_status()
metrics = sdk.get_metrics()
health = sdk.health_check()
```

### Command Line Interface

```bash
# CLI Tools
rag-pipeline --help
rag-pipeline process /path/to/pdfs --workers 4 --quality 80
rag-pipeline query "SharePoint config" --limit 10 --format json
rag-pipeline status --detailed
rag-pipeline deploy --replicas 3 --memory 4Gi
```

Diese umfassende API-Referenz ermöglicht es Entwicklern, die SharePoint RAG Pipeline vollständig zu verstehen, zu erweitern und in bestehende Systeme zu integrieren.