"""Utility helpers for environment setup, logging, and date parsing."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src import config


def initialize_environment() -> None:
    """Ensure required project data directories exist."""
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging format and level."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def ensure_directory(path: Path) -> None:
    """Create a directory path if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def parse_date(value: str | None) -> datetime:
    """Parse an ISO date string and return datetime.min on invalid input."""
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min