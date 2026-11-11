# Project record

## Objective

Incremental BM25 index with add, update and remove, multilingual analysis with diacritic folding and CJK bigrams, and atomic JSON persistence without pickle

## Scope

- In scope: the public API documented in [README.md](../README.md), typed and tested.
- Out of scope: anything that needs runtime dependencies or I/O without an accepted ADR.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 624312 / 65719 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0991 |

## Factory run u212 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | generation | deepseek-v4-pro | yes | 1714 | 23955 | 0 | 3328 | 0.0486 |
| 2026-11-11 | fix-1 | deepseek-flash | no | 11293 | 5666 | 0 | 68864 | 0.0053 |
| 2026-11-11 | fix-2 | deepseek-flash | no | 8160 | 2200 | 0 | 27008 | 0.0026 |
| 2026-11-11 | audit | deepseek-flash | no | 24195 | 21864 | 0 | 309376 | 0.0177 |
| 2026-11-11 | fix-3 | deepseek-flash | no | 9837 | 2288 | 0 | 53632 | 0.0030 |
| 2026-11-11 | docs | deepseek-flash | no | 106649 | 9746 | 0 | 256 | 0.0218 |

Total: $0.0991. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
