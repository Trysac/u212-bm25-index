"""Tests for save/load functionality."""

from __future__ import annotations

import json

import pytest

from bm25_index import Analyzer, Bm25Error, BM25Index


def _make_index() -> BM25Index:
    analyzer = Analyzer(stopwords=frozenset({"the"}))
    index = BM25Index(analyzer)
    index.add("a", "the quick brown fox")
    index.add("b", "the lazy dog")
    index.add("c", "quick quick dog")
    return index


def test_save_load_roundtrip(tmp_path) -> None:
    index = _make_index()
    path = tmp_path / "index.json"
    index.save(path)
    loaded = BM25Index.load(path)
    assert len(loaded) == len(index)
    for query in ["quick dog", "quick", "the", "cat"]:
        assert loaded.search(query) == index.search(query)


def test_save_file_format(tmp_path) -> None:
    index = _make_index()
    path = tmp_path / "index.json"
    index.save(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["format"] == "bm25-index"
    assert data["version"] == 1
    assert "docs" in data
    # Ensure no document text present
    for doc_data in data["docs"].values():
        assert set(doc_data.keys()) == {"len", "tf"}


def test_load_corrupt_json(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not json")
    with pytest.raises(Bm25Error) as exc_info:
        BM25Index.load(path)
    assert exc_info.value.code == "corrupt"


def test_load_wrong_version(tmp_path) -> None:
    path = tmp_path / "bad_version.json"
    data = {"format": "bm25-index", "version": 2, "k1": 1.2, "b": 0.75, "analyzer": {}, "docs": {}}
    path.write_text(json.dumps(data))
    with pytest.raises(Bm25Error) as exc_info:
        BM25Index.load(path)
    assert exc_info.value.code == "corrupt"


def test_load_negative_tf(tmp_path) -> None:
    path = tmp_path / "neg_tf.json"
    data = {
        "format": "bm25-index",
        "version": 1,
        "k1": 1.2,
        "b": 0.75,
        "analyzer": Analyzer().to_dict(),
        "docs": {"a": {"len": 1, "tf": {"token": -1}}},
    }
    path.write_text(json.dumps(data))
    with pytest.raises(Bm25Error) as exc_info:
        BM25Index.load(path)
    assert exc_info.value.code == "corrupt"


def test_load_length_mismatch(tmp_path) -> None:
    path = tmp_path / "mismatch.json"
    data = {
        "format": "bm25-index",
        "version": 1,
        "k1": 1.2,
        "b": 0.75,
        "analyzer": Analyzer().to_dict(),
        "docs": {"a": {"len": 2, "tf": {"token": 1}}},
    }
    path.write_text(json.dumps(data))
    with pytest.raises(Bm25Error) as exc_info:
        BM25Index.load(path)
    assert exc_info.value.code == "corrupt"


def test_load_missing_fields(tmp_path) -> None:
    path = tmp_path / "missing.json"
    data = {"format": "bm25-index", "version": 1}
    path.write_text(json.dumps(data))
    with pytest.raises(Bm25Error) as exc_info:
        BM25Index.load(path)
    assert exc_info.value.code == "corrupt"


def test_load_file_too_large(tmp_path) -> None:
    path = tmp_path / "large.json"
    # Create a file larger than max_file_bytes
    content = "x" * 1000
    path.write_text(content)
    with pytest.raises(Bm25Error) as exc_info:
        BM25Index.load(path, max_file_bytes=100)
    assert exc_info.value.code == "input_too_large"


def test_load_preserves_analyzer_settings(tmp_path) -> None:
    analyzer = Analyzer(stopwords=frozenset({"the"}), fold_diacritics=False, cjk_bigrams=False)
    index = BM25Index(analyzer)
    index.add("a", "Café the 東京")
    path = tmp_path / "index.json"
    index.save(path)
    loaded = BM25Index.load(path)
    assert loaded.analyzer.stopwords == analyzer.stopwords
    assert loaded.analyzer.fold_diacritics == analyzer.fold_diacritics
    assert loaded.analyzer.cjk_bigrams == analyzer.cjk_bigrams
