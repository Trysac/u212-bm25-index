"""BM25 index with incremental updates and persistence."""

from __future__ import annotations

import json
import math
import os
import tempfile
from collections.abc import Mapping
from typing import Any, NamedTuple

from .analyzer import Analyzer
from .errors import Bm25Error


class Hit(NamedTuple):
    doc_id: str
    score: float


class BM25Index:
    """Incremental Okapi BM25 index."""

    def __init__(
        self,
        analyzer: Analyzer | None = None,
        *,
        k1: float = 1.2,
        b: float = 0.75,
        max_docs: int = 1_000_000,
    ) -> None:
        if k1 < 0:
            raise Bm25Error("invalid_argument", "k1 must be >= 0")
        if not 0 <= b <= 1:
            raise Bm25Error("invalid_argument", "b must be in [0, 1]")
        if max_docs < 1:
            raise Bm25Error("invalid_argument", "max_docs must be >= 1")
        self.k1 = float(k1)
        self.b = float(b)
        self.max_docs = max_docs
        self.analyzer = analyzer or Analyzer()
        self._postings: dict[str, dict[str, int]] = {}
        self._doc_lengths: dict[str, int] = {}
        self._total_length = 0

    def __len__(self) -> int:
        return len(self._doc_lengths)

    def __contains__(self, doc_id: object) -> bool:
        return doc_id in self._doc_lengths

    @property
    def postings(self) -> Mapping[str, Mapping[str, int]]:
        """Read-only view of term postings (for tests and introspection)."""
        return self._postings

    def add(self, doc_id: str, text: str) -> None:
        """Add or update a document."""
        if not isinstance(doc_id, str) or not (1 <= len(doc_id) <= 256):
            raise Bm25Error(
                "invalid_id", f"doc_id must be a string of 1-256 characters, got {doc_id!r}"
            )
        if not isinstance(text, str):
            raise Bm25Error("invalid_argument", "text must be a string")
        if len(text) > 1_000_000:
            raise Bm25Error("input_too_large", "text exceeds 1,000,000 characters")

        # If updating, remove old stats first
        if doc_id in self._doc_lengths:
            self._remove_doc_internal(doc_id)
        else:
            if len(self._doc_lengths) >= self.max_docs:
                raise Bm25Error(
                    "index_full", f"maximum number of documents ({self.max_docs}) reached"
                )

        tokens = self.analyzer.analyze(text)
        length = len(tokens)
        self._doc_lengths[doc_id] = length
        self._total_length += length

        tf_map: dict[str, int] = {}
        for token in tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        for term, count in tf_map.items():
            postings_for_term = self._postings.setdefault(term, {})
            postings_for_term[doc_id] = count

    def remove(self, doc_id: str) -> bool:
        """Remove a document; returns True if it existed."""
        if doc_id not in self._doc_lengths:
            return False
        self._remove_doc_internal(doc_id)
        return True

    def _remove_doc_internal(self, doc_id: str) -> None:
        length = self._doc_lengths.pop(doc_id)
        self._total_length -= length
        terms_to_delete: list[str] = []
        for term, postings_for_term in self._postings.items():
            if doc_id in postings_for_term:
                del postings_for_term[doc_id]
                if not postings_for_term:
                    terms_to_delete.append(term)
        for term in terms_to_delete:
            del self._postings[term]

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Return up to ``k`` hits for ``query``, sorted by score descending then doc_id."""
        if not isinstance(query, str):
            raise Bm25Error("invalid_argument", "query must be a string")
        if len(query) > 10_000:
            raise Bm25Error("input_too_large", "query exceeds 10,000 characters")
        if not isinstance(k, int):
            raise Bm25Error("invalid_argument", "k must be an integer")
        if not 1 <= k <= 1000:
            raise Bm25Error("invalid_argument", "k must be an integer in [1, 1000]")

        query_terms = list(dict.fromkeys(self.analyzer.analyze(query)))
        if not query_terms or not self._doc_lengths or self._total_length == 0:
            return []

        avgdl = self._total_length / len(self._doc_lengths)
        scores: dict[str, float] = {}

        for term in query_terms:
            if term not in self._postings:
                continue
            postings_for_term = self._postings[term]
            n_t = len(postings_for_term)
            idf = math.log(1 + (len(self._doc_lengths) - n_t + 0.5) / (n_t + 0.5))
            for doc_id, tf in postings_for_term.items():
                dl = self._doc_lengths[doc_id]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / avgdl)
                score_inc = idf * tf * (self.k1 + 1) / denom
                scores[doc_id] = scores.get(doc_id, 0.0) + score_inc

        if not scores:
            return []
        positive_scores = {doc_id: score for doc_id, score in scores.items() if score > 0}
        if not positive_scores:
            return []
        sorted_docs = sorted(positive_scores.keys(), key=lambda d: (-positive_scores[d], d))
        return [Hit(doc_id=d, score=positive_scores[d]) for d in sorted_docs[:k]]

    def save(self, path: str | os.PathLike[str]) -> None:
        """Save index to a JSON file atomically."""
        target = os.fspath(path)
        data: dict[str, Any] = {
            "format": "bm25-index",
            "version": 1,
            "k1": self.k1,
            "b": self.b,
            "analyzer": self.analyzer.to_dict(),
            "docs": {},
        }
        docs: dict[str, dict[str, Any]] = {}
        for doc_id in sorted(self._doc_lengths):
            tf_map: dict[str, int] = {}
            for term, postings_for_term in self._postings.items():
                if doc_id in postings_for_term:
                    tf_map[term] = postings_for_term[doc_id]
            docs[doc_id] = {
                "len": self._doc_lengths[doc_id],
                "tf": {term: tf_map[term] for term in sorted(tf_map)},
            }
        data["docs"] = docs

        dir_name = os.path.dirname(target) or "."
        fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=os.path.basename(target) + ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target)
        except BaseException:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    @classmethod
    def load(
        cls,
        path: str | os.PathLike[str],
        *,
        max_file_bytes: int = 1_073_741_824,
    ) -> BM25Index:
        """Load an index from a JSON file created by :meth:`save`."""
        target = os.fspath(path)
        file_size = os.path.getsize(target)
        if file_size > max_file_bytes:
            raise Bm25Error("input_too_large", f"file size {file_size} exceeds {max_file_bytes}")

        with open(target, encoding="utf-8") as f:
            raw = f.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise Bm25Error("corrupt", "invalid JSON") from None

        if not isinstance(data, dict):
            raise Bm25Error("corrupt", "top-level JSON must be an object")
        if data.get("format") != "bm25-index":
            raise Bm25Error("corrupt", "missing or wrong format field")
        if data.get("version") != 1:
            raise Bm25Error("corrupt", "unsupported version")
        k1 = data.get("k1")
        b = data.get("b")
        if not isinstance(k1, (int, float)) or k1 < 0:
            raise Bm25Error("corrupt", "k1 missing or invalid")
        if not isinstance(b, (int, float)) or not (0 <= b <= 1):
            raise Bm25Error("corrupt", "b missing or invalid")
        analyzer_data = data.get("analyzer")
        if not isinstance(analyzer_data, dict):
            raise Bm25Error("corrupt", "analyzer missing or invalid")
        try:
            analyzer = Analyzer.from_dict(analyzer_data)
        except (TypeError, ValueError):
            raise Bm25Error("corrupt", "analyzer missing or invalid") from None
        docs_data = data.get("docs")
        if not isinstance(docs_data, dict):
            raise Bm25Error("corrupt", "docs missing or invalid")

        postings: dict[str, dict[str, int]] = {}
        doc_lengths: dict[str, int] = {}
        total_length = 0

        for doc_id, doc_data in docs_data.items():
            if not isinstance(doc_id, str) or not (1 <= len(doc_id) <= 256):
                raise Bm25Error("corrupt", "invalid doc_id")
            if not isinstance(doc_data, dict):
                raise Bm25Error("corrupt", f"invalid document data for {doc_id}")
            length = doc_data.get("len")
            tf_data = doc_data.get("tf")
            if not isinstance(length, int) or length < 0:
                raise Bm25Error("corrupt", f"invalid length for {doc_id}")
            if not isinstance(tf_data, dict):
                raise Bm25Error("corrupt", f"invalid tf for {doc_id}")
            tf_sum = 0
            for term, count in tf_data.items():
                if not isinstance(term, str):
                    raise Bm25Error("corrupt", f"invalid term in {doc_id}")
                if not isinstance(count, int) or count < 0:
                    raise Bm25Error("corrupt", f"invalid count for {term} in {doc_id}")
                tf_sum += count
                postings.setdefault(term, {})[doc_id] = count
            if tf_sum != length:
                raise Bm25Error("corrupt", f"doc length mismatch for {doc_id}")
            doc_lengths[doc_id] = length
            total_length += length

        index = cls.__new__(cls)
        index.k1 = float(k1)
        index.b = float(b)
        index.max_docs = 1_000_000
        index.analyzer = analyzer
        index._postings = postings
        index._doc_lengths = doc_lengths
        index._total_length = total_length
        return index
