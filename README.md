# trysac-bm25-index

`trysac-bm25-index` is an incremental Okapi BM25 ranking library for Python. It supports adding, updating and removing documents on the fly, multilingual text analysis with diacritic folding and CJK bigrams, and safe, inspectable JSON persistence (no pickle).

## Features

- Incremental postings: `add` / `remove` / update a document without rebuilding the whole index.
- Multilingual analysis: NFKC and casefold; optional diacritic folding; CJK script detection with overlapping bigrams for Chinese, Japanese and Korean text.
- Okapi BM25 scoring with Lucene's non-negative IDF.
- Atomic JSON save/load with validation and size limits.
- Typed, dependency-free (Python >= 3.10).

## Installation

```bash
pip install trysac-bm25-index
```

## Usage

```python
from bm25_index import Analyzer, BM25Index

analyzer = Analyzer(stopwords=frozenset({"the"}))
index = BM25Index(analyzer)
index.add("a", "the quick brown fox")
index.add("b", "the lazy dog")
index.add("c", "quick quick dog")

hits = index.search("quick dog", k=10)
print(hits)  # [Hit(doc_id='c', score=1.071...), ...]

index.save("index.json")
loaded = BM25Index.load("index.json")
```

See the [API documentation](https://pypi.org/project/trysac-bm25-index/) for details.

## Development

This project uses `uv` for dependency management and gate checks. See `AGENTS.md` for commands.
