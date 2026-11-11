# bm25-index

[![PyPI version](https://img.shields.io/pypi/v/trysac-bm25-index)](https://pypi.org/project/trysac-bm25-index/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-bm25-index)](LICENSE)
[![CI](https://github.com/Trysac/u212-bm25-index/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u212-bm25-index/actions/workflows/ci.yml)

Incremental BM25 index with add, update and remove, multilingual analysis with diacritic folding and CJK bigrams, and atomic JSON persistence without pickle

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-bm25-index
# or
uv add trysac-bm25-index
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import bm25_index

# normalize() trims surrounding whitespace and lower-cases the text.
print(bm25_index.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    bm25_index.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
