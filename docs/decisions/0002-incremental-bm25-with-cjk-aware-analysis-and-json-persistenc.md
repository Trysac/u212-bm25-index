# Incremental BM25 with CJK-aware analysis and JSON persistence

Status: accepted (generated, pending human review)

## Context

Small RAG and search projects need lexical ranking but existing BM25 libraries either rebuild the model on every change, lack CJK support, or use unsafe persistence like pickle.

## Decision

Implement an incremental BM25 index with an Analyzer that performs NFKC/casefold/diacritic folding and CJK bigrams, and persist state as validated JSON with atomic writes.

## Consequences

Users can add, update and remove documents efficiently; multilingual text is tokenized sensibly; persistence is safe and inspectable. The library remains dependency-free and single-writer.
