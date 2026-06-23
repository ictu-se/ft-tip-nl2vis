# Expanded Metadata-Aware LoRA Smoke Result

## Purpose

This smoke run tests whether Paper 09 can move beyond the small 1,200-task prototype and train on the expanded local dataset corpus while using explicit temporal-support metadata.

## Corpus

- Metadata datasets inventoried: 783
- Usable CSV-backed datasets: 783
- Intent records: 21,153
- Hard-negative temporal ranking pairs: 60,340
- Grouped split policy: by `dataset_id`, stratified by domain and `year_max` bucket
- Train: 14,773 records from 547 datasets
- Dev: 3,269 records from 121 datasets
- Test: 3,111 records from 115 datasets
- Test split has not been used.

## Training Setup

- Base model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- Fine-tuning: LoRA, 5.276M trainable parameters / 1.544B total parameters (0.342%)
- Training file: `benchmark_expanded/paper09_expanded_train_with_temporal_metadata_sft.jsonl`
- Validation file: first 512 records from expanded dev, used only for smoke loss monitoring
- Iterations: 300
- Batch size: 1
- Learning rate: `1e-5`
- Prompt masking: enabled
- Max sequence length: 2048
- Seed: 20260619
- Adapter: `training/adapters/qwen25_15b_expanded_metadata_smoke`

## Loss Trace

| Iteration | Validation loss | Train loss | Peak memory |
|---:|---:|---:|---:|
| 1 | 2.118 | - | - |
| 50 | - | 0.321 | 2.880 GB |
| 100 | 0.022 | 0.052 | 3.128 GB |
| 200 | 0.009 | 0.010 | 3.128 GB |
| 300 | 0.009 | 0.004 | 3.160 GB |

## Structured Dev64 Slice

This is a quick structured inference check, not the final dev result. The evaluated slice is the first 64 expanded-dev SFT records.

| Metric | Value |
|---|---:|
| JSON validity | 100.00% |
| Answerability accuracy | 87.50% |
| Task type accuracy | 90.625% |
| Required-field F1 | 0.875 |
| Time-field accuracy | 87.50% |
| Measure accuracy | 87.50% |
| Temporal-filter accuracy | 96.875% |
| Statistic accuracy | 98.4375% |
| Core-intent exact match | 87.50% |
| Full-intent exact match | 85.9375% |

## Main Failure Signal

The important failure is not JSON formatting. The adapter still tends to answer unsupported monthly-granularity requests instead of marking them unanswerable. Example: a monthly fertility-rate request is predicted as an answerable temporal trend with `temporal_filter="monthly"` even though the gold intent is `answerability="unanswerable"` with an unsupported-granularity reason.

## Decision

The expanded corpus and metadata-aware LoRA pipeline are viable. The next serious ablation should not simply train longer; it should target unsupported-intent detection and temporal-boundary discrimination:

- schema-only LoRA vs temporal-metadata-aware LoRA;
- temporal-metadata-aware LoRA with hard-negative unsupported examples;
- optional ranking/margin objective over the 60,340 temporal hard-negative pairs;
- full dev evaluation with the checkpointed/resumable inference script;
- final test only after checkpoint selection is frozen.
