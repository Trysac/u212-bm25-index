"""Incremental BM25 index with multilingual analysis and safe persistence."""

from __future__ import annotations

import logging

from .analyzer import Analyzer
from .errors import Bm25Error
from .index import BM25Index, Hit

__all__ = ["Analyzer", "BM25Index", "Bm25Error", "Hit", "__version__"]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
