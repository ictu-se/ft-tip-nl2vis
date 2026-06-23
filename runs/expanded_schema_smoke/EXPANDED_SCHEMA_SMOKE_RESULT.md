# Expanded Schema-Only LoRA Smoke Result

## Purpose

This run is the first direct ablation against the temporal-metadata-aware
expanded LoRA smoke run. It tests the mathematical claim that schema fields
alone are insufficient for temporal-boundary reasoning when datasets have
different temporal supports.

## Training Setup

- Base model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- Fine-tuning: LoRA, 5.276M trainable parameters / 1.544B total parameters
- Training file: `benchmark_expanded/paper09_expanded_train_schema_only_sft.jsonl`
- Validation file: first 512 records from expanded dev, schema-only format
- Iterations: 300
- Batch size: 1
- Learning rate: `1e-5`
- Prompt masking: enabled
- Max sequence length: 2048
- Seed: 20260619
- Adapter: `training/adapters/qwen25_15b_expanded_schema_smoke`

## Loss Trace

| Iteration | Validation loss | Train loss | Peak memory |
|---:|---:|---:|---:|
| 1 | 2.181 | - | - |
| 50 | - | 0.344 | 2.449 GB |
| 100 | 0.032 | 0.059 | 2.735 GB |
| 200 | 0.020 | 0.014 | 2.735 GB |
| 300 | 0.018 | 0.006 | 2.756 GB |

## Structured Dev64 Slice

| Metric | Schema-only | Temporal metadata |
|---|---:|---:|
| JSON validity | 100.00% | 100.00% |
| Answerability accuracy | 87.50% | 87.50% |
| Task type accuracy | 90.625% | 90.625% |
| Required-field F1 | 0.875 | 0.875 |
| Time-field accuracy | 87.50% | 87.50% |
| Measure accuracy | 87.50% | 87.50% |
| Temporal-filter accuracy | 68.75% | 96.875% |
| Statistic accuracy | 96.875% | 98.4375% |
| Core-intent exact match | 62.50% | 87.50% |
| Full-intent exact match | 62.50% | 85.9375% |

## Failure Signal

The schema-only adapter fails mainly on temporal-boundary-sensitive tasks:

- `temporal_recent_window`: 5 core failures;
- `temporal_previous_window`: 5 core failures;
- `temporal_boundary_check`: 4 core failures;
- `mixed_change_ranking`: 2 core failures.

The metadata-aware adapter removes nearly all temporal-filter failures on the
same dev64 slice. Its remaining failures are concentrated in unsupported
requests, not temporal-boundary prediction. This supports the paper's central
claim: temporal support metadata directly attacks the boundary-grounding
failure mode, while a separate answerability/gate objective is still needed for
unsupported requests.
