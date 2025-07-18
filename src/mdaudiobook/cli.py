#!/usr/bin/env python3
"""
Main CLI entry point for mdaudiobook pipeline
Orchestrates the complete Markdown to Audiobook conversion process
"""

import sys
import argparse
from pathlib import Path
import yaml
import json
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Import from mdaudiobook package (proper package imports)
from mdaudiobook.markdown_processor import MarkdownProcessor
from mdaudiobook.text_enhancer import TextEnhancer
from mdaudiobook.audiobook_generator import AudiobookGenerator


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if config_path is None:
        # Try default locations
        possible_configs = [
            Path('config/default.yaml'),
            Path('config.yaml'),
            Path.home() / '.config' / 'mdaudiobook' / 'config.yaml'
        ]
        
        for config_file in possible_configs:
            if config_file.exists():
                config_path = config_file
                break
        else:
            # Use default configuration
            return {
                'processing': {
                    'mode': 'hybrid',
                    'chunk_size': 1000,
                    'overlap': 100
                },
                'audio': {
                    'output_format': 'm4b',
                    'quality': 'high'
                }
            }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def extract_metadata(doc_structure, config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from document structure"""
    metadata = {
        'title': doc_structure.metadata.get('title', doc_structure.title),
        'author': doc_structure.metadata.get('author', 'Unknown Author'),
        'description': doc_structure.metadata.get('description', ''),
        'chapters': len(doc_structure.chapters),
        'processing_mode': config.get('processing', {}).get('mode', 'hybrid')
    }
    return metadata


def main():
    """Main CLI entry point for mdaudiobook."""
    parser = argparse.ArgumentParser(
        description="Professional Markdown to Audiobook Pipeline for Academic and Technical Content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mdaudiobook document.md
  mdaudiobook document.md --output-dir ./audiobooks
  mdaudiobook document.md --config custom.yaml --mode api
  mdaudiobook document.md --verbose --dry-run

Processing Modes:
  basic     - Simple text-to-speech conversion
  local-ai  - Enhanced processing with local AI models
  api       - Cloud-based processing with external APIs
  hybrid    - Combination of local and cloud processing (default)
        """
    )
    
    parser.add_argument(
        "input_file",
        type=Path,
        help="The path to the input Markdown file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory where the audiobook files will be saved (defaults to current directory)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode",
        choices=["basic", "local-ai", "api", "hybrid"],
        default="hybrid",
        help="Processing mode (default: hybrid)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually processing"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Validate input file
        if not args.input_file.exists():
            print(f"Error: Input file '{args.input_file}' does not exist")
            sys.exit(1)
        
        if not args.input_file.suffix.lower() in ['.md', '.markdown']:
            print(f"Error: Input file must be a Markdown file (.md or .markdown)")
            sys.exit(1)
        
        # Create output directory
        args.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        config = load_config(args.config)
        
        # Override mode if specified
        if args.mode != "hybrid":
            config.setdefault('processing', {})['mode'] = args.mode
        
        processing_mode = config.get('processing', {}).get('mode', 'hybrid')
        
        if args.verbose:
            print(f"mdaudiobook - Professional Markdown to Audiobook Pipeline")
            print(f"Input: {args.input_file}")
            print(f"Output Directory: {args.output_dir}")
            print(f"Processing Mode: {processing_mode}")
            print(f"Configuration: {args.config or 'default'}")
            print("-" * 60)
        
        # Generate output filename
        output_path = args.output_dir / f"{args.input_file.stem}.m4b"
        
        # Stage 1: Markdown Processing
        print("Stage 1: Processing markdown...")
        markdown_processor = MarkdownProcessor(config)
        
        doc_structure = markdown_processor.process_document(args.input_file)
        
        if args.verbose:
            print(f"  - Processed {len(doc_structure.chapters)} chapters")
            print(f"  - Document title: {doc_structure.title}")
            print(f"  - Math expressions: {len(doc_structure.math_expressions)}")
            print(f"  - Citations: {len(doc_structure.citations)}")
        
        # Stage 2: Text Enhancement
        print("Stage 2: Enhancing text for audio...")
        text_enhancer = TextEnhancer(config, processing_mode)
        
        enhanced_text = text_enhancer.enhance_document(doc_structure)
        
        # Validate enhanced text
        is_valid, issues = text_enhancer.validate_enhancement(enhanced_text)
        if not is_valid:
            print("Warning: Text enhancement issues detected:")
            for issue in issues:
                print(f"  - {issue}")
        
        if args.verbose:
            print(f"  - Enhanced text length: {len(enhanced_text.content)} characters")
            print(f"  - Voice assignments: {len(enhanced_text.voice_assignments)}")
            print(f"  - Chapter breaks: {len(enhanced_text.chapter_breaks)}")
        
        if args.dry_run:
            print("\nDRY RUN COMPLETE")
            print(f"Would generate audiobook: {output_path}")
            sys.exit(0)
        
        # Stage 3: Audio Generation
        print("Stage 3: Generating audiobook...")
        audiobook_generator = AudiobookGenerator(config, processing_mode)
        
        try:
            # Extract metadata
            metadata = extract_metadata(doc_structure, config)
            
            # Generate audiobook
            audiobook = audiobook_generator.generate_audiobook(
                enhanced_text, metadata, output_path
            )
            
            if args.verbose:
                print(f"  - Generated {len(audiobook.chapters)} audio chapters")
                print(f"  - Total duration: {len(audiobook.audio) / 1000:.1f} seconds")
                print(f"  - Output format: {config.get('audio', {}).get('output_format', 'm4b').upper()}")
            
            print("-" * 60)
            print("SUCCESS: Audiobook generation complete!")
            print(f"Output: {audiobook.file_path}")
            
            # Print chapter information
            if audiobook.chapters:
                print(f"\nChapters ({len(audiobook.chapters)}):")
                for chapter in audiobook.chapters:
                    duration_str = f"{chapter.duration:.1f}s"
                    print(f"  {chapter.chapter_number:2d}. {chapter.title} ({duration_str})")
        
        finally:
            # Cleanup temporary files
            audiobook_generator.cleanup()
    
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
