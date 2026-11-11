"""Tests for the Analyzer class."""

from __future__ import annotations

import pytest

from bm25_index import Analyzer


def test_diacritic_folding() -> None:
    analyzer = Analyzer()
    assert analyzer.analyze("Café") == ["cafe"]
    assert analyzer.analyze("Crème brûlée") == ["creme", "brulee"]


def test_no_diacritic_folding() -> None:
    analyzer = Analyzer(fold_diacritics=False)
    assert analyzer.analyze("Café") == ["café"]


def test_cjk_bigrams() -> None:
    analyzer = Analyzer()
    assert analyzer.analyze("東京") == ["東京"]
    assert analyzer.analyze("東京都の天気") == ["東京", "京都", "都の", "の天", "天気"]


def test_acceptance_diacritic_and_cjk_literals() -> None:
    analyzer = Analyzer()
    assert analyzer.analyze("Caf\u00e9 \u6771\u4eac") == ["cafe", "\u6771\u4eac"]
    assert analyzer.analyze("\u6771\u4eac\u90fd\u306e\u5929\u6c17") == [
        "\u6771\u4eac",
        "\u4eac\u90fd",
        "\u90fd\u306e",
        "\u306e\u5929",
        "\u5929\u6c17",
    ]


def test_cjk_single_char_unigram() -> None:
    analyzer = Analyzer()
    assert analyzer.analyze("東") == ["東"]


def test_cjk_bigrams_disabled() -> None:
    analyzer = Analyzer(cjk_bigrams=False)
    assert analyzer.analyze("東京") == ["東京"]
    assert analyzer.analyze("東京都の天気") == ["東京都の天気"]


def test_mixed_token_split() -> None:
    analyzer = Analyzer()
    assert analyzer.analyze("abc東京") == ["abc", "東京"]
    assert analyzer.analyze("東京123") == ["東京", "123"]
    assert analyzer.analyze("a東京b") == ["a", "東京", "b"]


def test_stopword_removal() -> None:
    analyzer = Analyzer(stopwords=frozenset({"the"}))
    assert analyzer.analyze("The quick brown fox") == ["quick", "brown", "fox"]


def test_stopwords_are_folded_before_comparison() -> None:
    analyzer = Analyzer(stopwords=frozenset({"Café", "THE"}))
    assert analyzer.analyze("café the") == []
    assert analyzer.analyze("Café THE quick") == ["quick"]
    # Raw stopwords are preserved for serialization
    assert analyzer.stopwords == frozenset({"Café", "THE"})


def test_to_dict_from_dict_roundtrip() -> None:
    original = Analyzer(stopwords=frozenset({"the", "a"}), fold_diacritics=False, cjk_bigrams=False)
    data = original.to_dict()
    restored = Analyzer.from_dict(data)
    assert restored.stopwords == original.stopwords
    assert restored.fold_diacritics == original.fold_diacritics
    assert restored.cjk_bigrams == original.cjk_bigrams


def test_from_dict_invalid_data() -> None:
    with pytest.raises(TypeError):
        Analyzer.from_dict("not a dict")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Analyzer.from_dict(
            {"stopwords": "not a list", "fold_diacritics": True, "cjk_bigrams": True}
        )
    with pytest.raises(ValueError):
        Analyzer.from_dict({"stopwords": [], "fold_diacritics": "yes", "cjk_bigrams": True})
    with pytest.raises(ValueError):
        Analyzer.from_dict({"stopwords": [], "fold_diacritics": True, "cjk_bigrams": "no"})
