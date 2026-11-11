"""Tests for BM25Index."""

from __future__ import annotations

import pytest

from bm25_index import Analyzer, Bm25Error, BM25Index


def _make_acceptance_index() -> BM25Index:
    analyzer = Analyzer(stopwords=frozenset({"the"}))
    index = BM25Index(analyzer)
    index.add("a", "the quick brown fox")
    index.add("b", "the lazy dog")
    index.add("c", "quick quick dog")
    return index


def test_acceptance_search_scores() -> None:
    index = _make_acceptance_index()
    hits = index.search("quick dog")
    assert [h.doc_id for h in hits] == ["c", "b", "a"]
    assert [round(h.score, 6) for h in hits] == [1.071445, 0.523548, 0.447139]


def test_acceptance_remove() -> None:
    index = _make_acceptance_index()
    assert index.remove("c") is True
    hits = index.search("quick")
    assert len(hits) == 1
    assert hits[0].doc_id == "a"
    assert round(hits[0].score, 6) == 0.640724
    assert len(index) == 2
    assert "c" not in index
    # Check no 'c' in any posting list
    for postings_for_term in index.postings.values():
        assert "c" not in postings_for_term


def test_acceptance_update_existing() -> None:
    index = _make_acceptance_index()
    index.add("a", "lazy cat")
    assert index.search("fox") == []
    assert [h.doc_id for h in index.search("cat")] == ["a"]


def test_ties_ordered_by_docid() -> None:
    index = BM25Index()
    index.add("b", "same text")
    index.add("a", "same text")
    hits = index.search("same")
    assert [h.doc_id for h in hits] == ["a", "b"]


def test_query_only_stopwords() -> None:
    index = _make_acceptance_index()
    assert index.search("the") == []


def test_score_never_zero() -> None:
    index = _make_acceptance_index()
    hits = index.search("quick", k=10)
    assert all(h.score > 0 for h in hits)


def test_k_validation() -> None:
    index = _make_acceptance_index()
    with pytest.raises(Bm25Error) as exc_info:
        index.search("quick", k=0)
    assert exc_info.value.code == "invalid_argument"
    with pytest.raises(Bm25Error) as exc_info:
        index.search("quick", k=1001)
    assert exc_info.value.code == "invalid_argument"
    with pytest.raises(Bm25Error) as exc_info:
        index.search("quick", k=1.5)  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_argument"


def test_add_validation() -> None:
    index = BM25Index(max_docs=2)
    with pytest.raises(Bm25Error) as exc_info:
        index.add("", "text")
    assert exc_info.value.code == "invalid_id"
    with pytest.raises(Bm25Error) as exc_info:
        index.add("x" * 257, "text")
    assert exc_info.value.code == "invalid_id"
    with pytest.raises(Bm25Error) as exc_info:
        index.add(123, "text")  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_id"
    with pytest.raises(Bm25Error) as exc_info:
        index.add("id", "x" * 1_000_001)
    assert exc_info.value.code == "input_too_large"
    # 1,000,000 characters accepted
    index.add("long", "x" * 1_000_000)
    # Now len=1, max_docs=2, adding new should be okay
    index.add("id2", "text")
    # Now len=2, adding new should fail
    with pytest.raises(Bm25Error) as exc_info:
        index.add("id3", "text")
    assert exc_info.value.code == "index_full"


def test_update_does_not_trigger_index_full() -> None:
    index = BM25Index(max_docs=1)
    index.add("a", "text")
    index.add("a", "other")
    assert len(index) == 1


def test_remove_last_document() -> None:
    index = BM25Index()
    index.add("a", "quick fox")
    assert index.remove("a") is True
    assert len(index) == 0
    assert "a" not in index
    assert index.search("quick") == []
    assert index.postings == {}


def test_remove_missing_returns_false() -> None:
    index = _make_acceptance_index()
    assert index.remove("nonexistent") is False


def test_len_and_contains() -> None:
    index = BM25Index()
    index.add("a", "text")
    assert len(index) == 1
    assert "a" in index
    assert "b" not in index


def test_b_zero() -> None:
    index = BM25Index(b=0.0)
    index.add("a", "short doc")
    index.add("b", "this is a much longer document with more terms")
    hits = index.search("terms")
    # With b=0, length normalization is ignored; scores depend only on tf/idf
    # Just check that search works and scores are positive
    assert hits and hits[0].score > 0


def test_empty_doc_not_returned() -> None:
    index = BM25Index(Analyzer(stopwords=frozenset({"the"})))
    index.add("empty", "the")
    assert len(index) == 1
    assert index.search("the") == []
    # No posting for 'the' should exist
    assert "the" not in index.postings


def test_fullwidth_digits_folding() -> None:
    index = BM25Index()
    index.add("a", "\uff11\uff12\uff13")
    assert [h.doc_id for h in index.search("123")] == ["a"]


def test_hangul_bigrams() -> None:
    analyzer = Analyzer()
    # Hangul syllables are CJK, so a 3+ syllable run yields overlapping bigrams
    assert analyzer.analyze("한국어") == ["한국", "국어"]
    assert Analyzer(cjk_bigrams=False).analyze("한국어") == ["한국어"]
