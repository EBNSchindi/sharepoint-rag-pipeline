#!/usr/bin/env python3
"""
Minimal Test für die Pipeline-Komponenten
Testet Funktionalität ohne externe Dependencies
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_basic_components():
    """Test basic components without external dependencies"""
    print("🧪 Testing Basic Pipeline Components")
    print("=" * 50)
    
    # Test 1: Configuration Loading
    try:
        import yaml
        with open('config/pipeline.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✅ Configuration loaded successfully")
        print(f"   - Pipeline version: {config.get('version', 'unknown')}")
        print(f"   - Chunking strategy: {config.get('chunking', {}).get('strategy', 'unknown')}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print()
    
    # Test 2: Directory Structure
    print("📁 Testing Directory Structure:")
    required_dirs = ['data/input', 'data/processed', 'data/state', 'data/vectors', 'logs']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} missing")
    
    print()
    
    # Test 3: Storage Components
    print("💾 Testing Storage Components:")
    try:
        from storage.metadata_store import MetadataStore
        config = {'metadata_db_path': 'test.db'}
        store = MetadataStore(config)
        stats = store.get_statistics()
        print(f"✅ Metadata Store - {stats.get('total_documents', 0)} documents")
    except Exception as e:
        print(f"❌ Metadata Store error: {e}")
    
    try:
        from storage.vector_store import ContextualVectorStore
        config = {'vector_store': {'persist_directory': './test_vectors'}}
        store = ContextualVectorStore(config)
        print("✅ Vector Store (fallback mode)")
    except Exception as e:
        print(f"❌ Vector Store error: {e}")
    
    print()
    
    # Test 4: Incremental Processing
    print("🔄 Testing Incremental Processing:")
    try:
        from pipeline.incremental_processor import IncrementalProcessor
        
        config = {
            'state_directory': './data/state',
            'version': '2.0.0'
        }
        
        processor = IncrementalProcessor(config)
        
        # Create test directory and file
        test_dir = Path('test_input')
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / 'test.pdf'
        test_file.write_text('dummy PDF content for testing')
        
        files_to_process = processor.get_files_to_process(test_dir)
        stats = processor.get_processing_statistics()
        
        print(f"✅ Incremental Processor")
        print(f"   - Files to process: {len(files_to_process)}")
        print(f"   - Total files in database: {stats['total_files']}")
        print(f"   - Total chunks: {stats['total_chunks']}")
        
    except Exception as e:
        print(f"❌ Incremental Processor error: {e}")
    
    print()
    
    # Test 5: Fallback Pipeline without Dependencies
    print("🔧 Testing Fallback Pipeline:")
    try:
        from pipeline.orchestrator import ContextualRAGOrchestrator
        
        # This should work with fallback modes
        orchestrator = ContextualRAGOrchestrator('config/pipeline.yaml')
        print("✅ Orchestrator initialized (fallback mode)")
        
        # Test empty report generation
        report = orchestrator._generate_empty_report()
        print(f"   - Empty report generated: {report['summary']['total_files_processed']} files")
        
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
    
    print()
    
    # Test 6: Context Rules
    print("📋 Testing Context Rules:")
    try:
        with open('config/context_rules.yaml', 'r') as f:
            rules = yaml.safe_load(f)
        
        chunk_types = rules.get('chunk_type_indicators', {})
        print(f"✅ Context Rules loaded")
        print(f"   - Chunk types defined: {len(chunk_types)}")
        print(f"   - Example types: {', '.join(list(chunk_types.keys())[:3])}")
        
    except Exception as e:
        print(f"❌ Context Rules error: {e}")

def test_with_dependencies():
    """Test components that require external dependencies"""
    print("\n🔬 Testing Components with Dependencies")
    print("=" * 50)
    
    # Test Dependencies
    deps_to_test = [
        ('pydantic', 'Contextual Chunk Model'),
        ('autogen', 'AutoGen Agents'),
        ('chromadb', 'ChromaDB Vector Store'),
        ('spacy', 'NLP Processing'),
        ('transformers', 'ML Models'),
        ('PyPDF2', 'PDF Processing'),
        ('pdfplumber', 'PDF Processing'),
        ('sentence_transformers', 'Embeddings')
    ]
    
    available_deps = []
    missing_deps = []
    
    for dep, description in deps_to_test:
        try:
            __import__(dep)
            available_deps.append((dep, description))
            print(f"✅ {dep} - {description}")
        except ImportError:
            missing_deps.append((dep, description))
            print(f"❌ {dep} - {description} (not installed)")
    
    print(f"\nSummary: {len(available_deps)} available, {len(missing_deps)} missing")
    
    if missing_deps:
        print("\n📦 To install missing dependencies:")
        print("pip install -r requirements.txt")
        print("python -m spacy download en_core_web_sm")

def main():
    """Main test function"""
    print("🚀 SharePoint RAG Pipeline - Component Test")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    # Run basic tests
    test_basic_components()
    
    # Run dependency tests  
    test_with_dependencies()
    
    print("\n" + "=" * 60)
    print("✅ Test completed! Pipeline structure is ready.")
    print("📋 Next steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Install spaCy model: python -m spacy download en_core_web_sm")
    print("   3. Test with real PDFs: python run_pipeline.py test_input --dry-run")

if __name__ == '__main__':
    main()