"""
CLI tools for the Image Frames API.

This package contains command-line utilities for data ingestion,
database management, and other administrative tasks.
"""

from app.cli.ingest import main as ingest_main

__all__ = ["ingest_main"]
