"""Text analysis for BM25 indexing."""

from __future__ import annotations

import unicodedata

_CJK_RANGES = [
    (0x3400, 0x4DBF),  # CJK Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3040, 0x309F),  # Hiragana
    (0x30A0, 0x30FF),  # Katakana
    (0xAC00, 0xD7AF),  # Hangul Syllables
]


def _is_cjk_char(ch: str) -> bool:
    cp = ord(ch)
    return any(start <= cp <= end for start, end in _CJK_RANGES)


class Analyzer:
    """Multilingual text analyzer with diacritic folding and CJK bigrams."""

    def __init__(
        self,
        *,
        stopwords: frozenset[str] = frozenset(),
        fold_diacritics: bool = True,
        cjk_bigrams: bool = True,
    ) -> None:
        self.stopwords = stopwords
        self.fold_diacritics = fold_diacritics
        self.cjk_bigrams = cjk_bigrams
        # Stopwords are compared in their folded form so that e.g. {"THE", "Café"}
        # filters "the" and "café" after the same normalization pipeline as the text.
        self._folded_stopwords = frozenset(self._fold(s) for s in stopwords)

    def _fold(self, text: str) -> str:
        """Apply NFKC, casefold and (optionally) diacritic folding to ``text``."""
        normalized = unicodedata.normalize("NFKC", text).casefold()
        if self.fold_diacritics:
            # NFD, remove combining marks (Mn), NFC
            decomposed = unicodedata.normalize("NFD", normalized)
            filtered = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
            normalized = unicodedata.normalize("NFC", filtered)
        return normalized

    def to_dict(self) -> dict[str, object]:
        return {
            "stopwords": sorted(self.stopwords),
            "fold_diacritics": self.fold_diacritics,
            "cjk_bigrams": self.cjk_bigrams,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Analyzer:
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")
        stopwords = data.get("stopwords")
        if not isinstance(stopwords, list) or not all(isinstance(s, str) for s in stopwords):
            raise ValueError("stopwords must be a list of strings")
        fold_diacritics = data.get("fold_diacritics")
        cjk_bigrams = data.get("cjk_bigrams")
        if not isinstance(fold_diacritics, bool) or not isinstance(cjk_bigrams, bool):
            raise ValueError("fold_diacritics and cjk_bigrams must be bool")
        return cls(
            stopwords=frozenset(stopwords),
            fold_diacritics=fold_diacritics,
            cjk_bigrams=cjk_bigrams,
        )

    def analyze(self, text: str) -> list[str]:
        """Return a list of tokens for ``text``."""
        # Normalize: NFKC, casefold, optional diacritic folding
        normalized = self._fold(text)

        # Tokenize into maximal runs of isalnum characters
        tokens: list[str] = []
        current: list[str] = []
        for ch in normalized:
            if ch.isalnum():
                current.append(ch)
            else:
                if current:
                    tokens.append("".join(current))
                    current = []
        if current:
            tokens.append("".join(current))

        # Process each token: split at script changes (CJK vs non-CJK), then bigram CJK runs
        processed_tokens: list[str] = []
        for token in tokens:
            if not token:
                continue
            # If all CJK, handle as single run
            if all(_is_cjk_char(ch) for ch in token):
                runs = [(token, True)]
            else:
                # Split into runs of same script category (CJK vs non-CJK)
                runs = []
                run_chars: list[str] = []
                run_is_cjk = _is_cjk_char(token[0])
                for ch in token:
                    ch_is_cjk = _is_cjk_char(ch)
                    if ch_is_cjk != run_is_cjk:
                        runs.append(("".join(run_chars), run_is_cjk))
                        run_chars = []
                        run_is_cjk = ch_is_cjk
                    run_chars.append(ch)
                if run_chars:
                    runs.append(("".join(run_chars), run_is_cjk))

            for run, is_cjk in runs:
                if is_cjk and self.cjk_bigrams and len(run) >= 2:
                    for i in range(len(run) - 1):
                        processed_tokens.append(run[i : i + 2])
                else:
                    processed_tokens.append(run)

        # Remove stopwords (compared in their folded form)
        return [t for t in processed_tokens if t not in self._folded_stopwords]
