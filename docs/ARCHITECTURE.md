# Architecture

## Overview

The library is split into three core modules:

- `bm25_index.errors`: `Bm25Error` with stable machine-readable codes.
- `bm25_index.analyzer`: `Analyzer` implements the text normalization and tokenization pipeline.
- `bm25_index.index`: `BM25Index` maintains incremental statistics, scoring, and persistence.

## Design Decisions

1. **Incremental statistics**: Postings, document lengths and total length are updated on each `add`/`remove`. This avoids rebuilding the index and supports updates by first removing old statistics.
2. **CJK-aware analysis**: Tokens consisting entirely of CJK characters (Han, Hiragana, Katakana, Hangul) are converted to overlapping bigrams when `cjk_bigrams=True`. Mixed tokens are split at script boundaries.
3. **Safe persistence**: JSON is used instead of pickle. Files are written atomically via `tempfile` + `os.replace` and validated on load, including size limit and structural checks.
4. **Validation limits**: Document IDs (1-256 chars), text (1e6 chars), query (1e4 chars), k (1-1000), max_docs. Oversized inputs raise `input_too_large`, invalid identifiers raise `invalid_id`, etc.

## Data Flow

1. `add(doc_id, text)` validates inputs, removes old stats if the ID exists, analyzes text into tokens, updates `_doc_lengths`, `_total_length` and `_postings`.
2. `search(query, k)` analyzes the query, computes IDF for each term, accumulates scores for matching documents, sorts by score then doc ID, and returns top-k results with positive scores.
3. `save(path)` serializes the index state to a sorted JSON structure; `load(path)` validates and reconstructs the in-memory structures.

## Threat Model

This is not a security library; however, inputs are untrusted and are bounded as described above. JSON is parsed with `json.loads` after a size check, and all fields are validated. No code execution is possible through loading because pickle is never used.
