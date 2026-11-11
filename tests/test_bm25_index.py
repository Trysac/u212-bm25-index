"""Behavior tests for the public API of bm25_index."""

from __future__ import annotations

import bm25_index
from bm25_index import Analyzer, Bm25Error, Hit


def test_public_api_exports() -> None:
    assert set(bm25_index.__all__) == {
        "Analyzer",
        "BM25Index",
        "Bm25Error",
        "Hit",
        "__version__",
    }


def test_analyzer_multilingual_analysis() -> None:
    assert Analyzer().analyze("Café 東京") == ["cafe", "東京"]


def test_hit_is_a_named_tuple() -> None:
    hit = Hit("a", 0.5)
    assert hit.doc_id == "a"
    assert hit.score == 0.5
    assert tuple(hit) == ("a", 0.5)


def test_error_exposes_stable_code() -> None:
    error = Bm25Error("invalid_id", "bad id")
    assert error.code == "invalid_id"


def test_readme_usage_example(tmp_path) -> None:
    from bm25_index import BM25Index

    analyzer = Analyzer(stopwords=frozenset({"the"}))
    index = BM25Index(analyzer)
    index.add("a", "the quick brown fox")
    index.add("b", "the lazy dog")
    index.add("c", "quick quick dog")

    hits = index.search("quick dog", k=10)
    assert [hit.doc_id for hit in hits] == ["c", "b", "a"]

    path = tmp_path / "index.json"
    index.save(path)
    loaded = BM25Index.load(path)
    assert loaded.search("quick dog", k=10) == hits


def test_version_is_semver() -> None:
    parts = bm25_index.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
