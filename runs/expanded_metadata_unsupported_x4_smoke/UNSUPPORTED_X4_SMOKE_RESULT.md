# Expanded Metadata-Aware Unsupported-x4 Smoke Result

## Purpose

This run tests whether increasing unsupported-request exposure reduces false
plotting. It directly targets the main failure mode of the metadata-aware smoke
adapter: monthly/future unsupported requests were sometimes predicted as
answerable.

## Data Policy

Training data starts from
`paper09_expanded_train_with_temporal_metadata_sft.jsonl`.

The oversampled training file keeps all 14,773 records and adds three extra
copies of every unanswerable record:

- original records: 14,773;
- original unsupported records: 2,188;
- final training records: 21,337;
- unsupported exposure after oversampling: 8,752 records;
- unsupported fraction after oversampling: 41.02%.

## Training Setup

- Base model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- Fine-tuning: LoRA, 5.276M trainable parameters / 1.544B total parameters
- Iterations: 300
- Batch size: 1
- Learning rate: `1e-5`
- Prompt masking: enabled
- Max sequence length: 2048
- Seed: 20260619
- Adapter: `training/adapters/qwen25_15b_expanded_metadata_unsupported_x4_smoke`

## Loss Trace

| Iteration | Validation loss | Train loss | Peak memory |
|---:|---:|---:|---:|
| 1 | 2.092 | - | - |
| 50 | - | 0.341 | 2.832 GB |
| 100 | 0.054 | 0.034 | 3.085 GB |
| 200 | 0.013 | 0.010 | 3.085 GB |
| 300 | 0.012 | 0.006 | 3.085 GB |

## Structured Dev64 Slice

| Metric | Metadata SFT | Unsupported-x4 |
|---|---:|---:|
| JSON validity | 100.00% | 100.00% |
| Answerability accuracy | 87.50% | 100.00% |
| Task-type accuracy | 90.625% | 95.3125% |
| Required-field F1 | 0.875 | 1.000 |
| Time-field accuracy | 87.50% | 100.00% |
| Measure accuracy | 87.50% | 100.00% |
| Temporal-filter accuracy | 96.875% | 92.1875% |
| Statistic accuracy | 98.4375% | 100.00% |
| Core-intent exact match | 87.50% | 87.50% |
| Full-intent exact match | 85.9375% | 87.50% |

## Interpretation

Unsupported oversampling eliminates the observed dev64 answerability failures:
the baseline metadata-aware adapter has 8 answerability failures, all false
plots on unsupported requests; the unsupported-x4 adapter has 0 answerability
failures on the same slice.

However, temporal-filter accuracy drops from 96.875% to 92.1875%. The remaining
core failures shift from unsupported requests to answerable temporal/statistical
tasks. This supports the need for the full FT-TIP objective rather than simple
oversampling alone:

```text
L_core = L_SFT + beta L_rank + gamma L_boundary + rho L_gate
```

The gate/unsupported pressure helps safety, but the boundary/ranking terms are
still needed to preserve temporal-filter fidelity.
