#!/usr/bin/env python3
"""
Contextual RAG Pipeline Runner
Führt die monatliche/halbjährliche Dokumentverarbeitung aus
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from pipeline.orchestrator import ContextualRAGOrchestrator
except ImportError as e:
    print(f"Error importing pipeline components: {e}")
    print("Please ensure all dependencies are installed and the project structure is correct.")
    sys.exit(1)

def setup_logging():
    """Setup basic logging for the runner"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def validate_input_directory(input_dir: str) -> Path:
    """Validate and return input directory path"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory does not exist: {input_path}")
        sys.exit(1)
    
    if not input_path.is_dir():
        print(f"Error: Input path is not a directory: {input_path}")
        sys.exit(1)
    
    # Check for PDF files
    pdf_files = list(input_path.glob('*.pdf'))
    if not pdf_files:
        print(f"Warning: No PDF files found in {input_path}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    else:
        print(f"Found {len(pdf_files)} PDF files in {input_path}")
    
    return input_path

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Run Contextual RAG Pipeline for SharePoint Knowledge Base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_pipeline.py /path/to/pdfs
  python run_pipeline.py /path/to/pdfs --force-all
  python run_pipeline.py /path/to/pdfs --workers 8 --config custom_config.yaml
  python run_pipeline.py /path/to/pdfs --dry-run
        '''
    )
    
    parser.add_argument(
        'input_directory',
        type=str,
        help='Directory containing PDF files to process'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/pipeline.yaml',
        help='Path to configuration file (default: config/pipeline.yaml)'
    )
    
    parser.add_argument(
        '--force-all',
        action='store_true',
        help='Force processing of all files (ignore incremental processing)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually processing'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset all processing state before running (use with caution)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration and setup, do not process files'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    
    # Print banner
    print("=" * 60)
    print("CONTEXTUAL RAG PIPELINE FOR SHAREPOINT")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input directory: {args.input_directory}")
    print(f"Configuration: {args.config}")
    print(f"Workers: {args.workers}")
    print(f"Force all: {args.force_all}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 60)
    
    # Validate input directory
    input_path = validate_input_directory(args.input_directory)
    
    # Validate configuration file
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Initialize orchestrator
    try:
        logger.info("Initializing pipeline orchestrator...")
        orchestrator = ContextualRAGOrchestrator(str(config_path))
        logger.info("Pipeline orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing pipeline: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Validation only mode
    if args.validate_only:
        print("\nValidation completed successfully!")
        print("Pipeline is ready to process documents.")
        sys.exit(0)
    
    # Reset processing state if requested
    if args.reset:
        print("\nResetting processing state...")
        response = input("This will delete all processing history. Continue? (y/N): ")
        if response.lower() == 'y':
            try:
                orchestrator.incremental_processor.reset_processing_state(confirm=True)
                print("Processing state reset successfully")
            except Exception as e:
                logger.error(f"Error resetting processing state: {e}")
                sys.exit(1)
        else:
            print("Reset cancelled")
            sys.exit(0)
    
    # Dry run mode
    if args.dry_run:
        print("\nDRY RUN - Would process the following files:")
        print("-" * 40)
        
        try:
            if args.force_all:
                files_to_process = list(input_path.glob('*.pdf'))
            else:
                files_to_process = orchestrator.incremental_processor.get_files_to_process(input_path)
            
            if not files_to_process:
                print("No files to process")
            else:
                for i, file_path in enumerate(files_to_process, 1):
                    print(f"{i:3d}. {file_path.name}")
                
                print(f"\nTotal: {len(files_to_process)} files")
                
                # Estimate processing time
                avg_time_per_file = 30  # seconds
                estimated_time = len(files_to_process) * avg_time_per_file / args.workers
                print(f"Estimated processing time: {estimated_time:.0f} seconds ({estimated_time/60:.1f} minutes)")
        
        except Exception as e:
            logger.error(f"Error during dry run: {e}")
            sys.exit(1)
        
        sys.exit(0)
    
    # Run pipeline
    try:
        print("\nStarting document processing...")
        print("=" * 40)
        
        start_time = datetime.now()
        
        report = orchestrator.process_documents(
            input_dir=str(input_path),
            force_all=args.force_all,
            max_workers=args.workers
        )
        
        end_time = datetime.now()
        processing_duration = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETED")
        print("=" * 60)
        print(f"Duration: {processing_duration}")
        print(f"Total files processed: {report['summary']['total_files_processed']}")
        print(f"Successful: {report['summary']['successful']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Total chunks created: {report['chunks']['total_created']}")
        print(f"Average chunks per document: {report['chunks']['average_per_document']:.1f}")
        print(f"Average quality score: {report['quality']['average_score']:.1f}")
        print(f"Quality range: {report['quality']['min_score']:.1f} - {report['quality']['max_score']:.1f}")
        
        # Show failures if any
        if report['failures']:
            print(f"\nFAILED FILES ({len(report['failures'])}):")
            print("-" * 40)
            for failure in report['failures']:
                print(f"  • {failure['file']}")
                print(f"    Error: {failure['error']}")
        
        # Show incremental processing stats
        incremental_stats = report.get('incremental_processing', {})
        if incremental_stats:
            print(f"\nINCREMENTAL PROCESSING STATISTICS:")
            print("-" * 40)
            stats = incremental_stats.get('statistics', {})
            print(f"Total documents in database: {stats.get('total_files', 0)}")
            print(f"Total chunks in database: {stats.get('total_chunks', 0)}")
            print(f"Average processing time: {stats.get('average_processing_time', 0):.1f}s")
        
        # Show recommendations
        if report['quality']['average_score'] < 80:
            print(f"\nRECOMMENDATIONS:")
            print("-" * 40)
            print("• Consider reviewing extraction settings for better quality")
            print("• Check if PDFs are text-based or require OCR")
            print("• Verify document format compatibility")
        
        print(f"\nProcessing completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Check the logs and reports directory for detailed information.")
        
        # Exit with appropriate code
        if report['summary']['failed'] > 0:
            print(f"\nWarning: {report['summary']['failed']} files failed to process")
            sys.exit(1)
        else:
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()