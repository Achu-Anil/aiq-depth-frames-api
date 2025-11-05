"""
Ingestion script to load CSV data into the database.

Usage:
    python -m scripts.ingest [csv_path] [--chunk-size 500]

Example:
    python -m scripts.ingest data/frames.csv --chunk-size 100
"""

import argparse
import asyncio
import sys
from pathlib import Path

from app.core import setup_logging, settings
from app.processing.ingest import ingest_csv


async def main():
    """Main ingestion entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest CSV frames into database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default CSV path from .env
  python -m scripts.ingest
  
  # Specify custom CSV path
  python -m scripts.ingest data/my_frames.csv
  
  # Custom chunk size for memory control
  python -m scripts.ingest data/frames.csv --chunk-size 100
  
  # Custom image dimensions
  python -m scripts.ingest --source-width 200 --target-width 150
        """
    )
    
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=None,
        help=f"Path to CSV file (default: {settings.csv_file_path})"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help=f"Number of rows to process per batch (default: {settings.chunk_size})"
    )
    
    parser.add_argument(
        "--source-width",
        type=int,
        default=200,
        help="Expected number of pixel columns in CSV (default: 200)"
    )
    
    parser.add_argument(
        "--target-width",
        type=int,
        default=150,
        help="Target image width after resize (default: 150)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Display configuration
    print("=" * 70)
    print("CSV INGESTION")
    print("=" * 70)
    print(f"CSV Path:      {args.csv_path or settings.csv_file_path}")
    print(f"Chunk Size:    {args.chunk_size or settings.chunk_size}")
    print(f"Source Width:  {args.source_width} pixels")
    print(f"Target Width:  {args.target_width} pixels")
    print(f"Database:      {settings.database_url}")
    print("=" * 70)
    print()
    
    try:
        # Run ingestion
        result = await ingest_csv(
            csv_path=args.csv_path,
            chunk_size=args.chunk_size,
            source_width=args.source_width,
            target_width=args.target_width
        )
        
        # Display results
        print()
        print("=" * 70)
        print("✅ INGESTION COMPLETE")
        print("=" * 70)
        print(f"Rows Processed:   {result['rows_processed']}")
        print(f"Frames Upserted:  {result['frames_upserted']}")
        print(f"Source Width:     {result['source_width']} pixels")
        print(f"Target Width:     {result['target_width']} pixels")
        print("=" * 70)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print(f"\nMake sure the CSV file exists at the specified path.", file=sys.stderr)
        return 1
        
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print(f"\nCheck that the CSV has the expected column structure.", file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
