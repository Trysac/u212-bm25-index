"""Error types for bm25_index."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal[
    "invalid_id",
    "invalid_argument",
    "input_too_large",
    "index_full",
    "corrupt",
]


class Bm25Error(ValueError):
    """Base error for the library with a stable machine-readable code."""

    def __init__(self, code: ErrorCode, message: str = "") -> None:
        self.code = code
        super().__init__(message if message else code)
