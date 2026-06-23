# Long Fine-Tune Result: Qwen2.5 1.5B LoRA

Date: 2026-06-19

## Model

Base model:

```text
mlx-community/Qwen2.5-1.5B-Instruct-4bit
```

Adapter:

```text
training/adapters/qwen25_15b_ft_tip_long
```

## Training Setup

- Fine-tune type: LoRA
- Iterations: 1000
- Batch size: 1
- Learning rate: `1e-5`
- Max sequence length: 2048
- Prompt masking: enabled
- Seed: 20260619
- Trainable parameters: 5.276M / 1543.714M, or 0.342%
- Peak memory: about 2.48 GB
- Checkpoints saved at 200, 400, 600, 800, and 1000 iterations.

## Validation Loss Trace

| Iteration | Validation Loss |
| ---: | ---: |
| 1 | 2.162 |
| 200 | 0.007 |
| 400 | 0.004 |
| 600 | 0.006 |
| 800 | 0.002 |
| 1000 | 0.002 |

## Dev Structured Metrics

Evaluated on all 184 Paper 09 dev records.

| Metric | Smoke 100 iters | Long 1000 iters |
| --- | ---: | ---: |
| JSON validity | 100.00% | 100.00% |
| answerability accuracy | 82.61% | 100.00% |
| task-type accuracy | 64.13% | 100.00% |
| required-field F1 | 0.8261 | 1.0000 |
| time-field accuracy | 82.61% | 100.00% |
| measure accuracy | 82.61% | 100.00% |
| temporal-filter accuracy | 80.43% | 95.11% |
| statistic accuracy | 89.67% | 100.00% |
| core-intent accuracy | 61.41% | 95.11% |
| full-intent accuracy | 57.07% | 95.11% |

## Remaining Errors

Only 9 dev records fail core intent after the long run. All failures are
temporal-filter mismatches:

- 6 `temporal_recent_window` cases;
- 3 `mixed_change_ranking` cases;
- 6 English prompts and 3 Vietnamese prompts.

The recurring pattern is that the model defaults to a memorized recent window
such as `2015-2024`, while the gold label depends on the dataset-specific year
range, e.g. `2016-2025`, `2014-2023`, or `2011-2020`.

Failure details:

```text
dev_core_failures.csv
```

## Interpretation

This is now a strong method signal for Paper 09. A compact Qwen2.5 1.5B model
with only LoRA adaptation improves dev core-intent accuracy from the Paper 08
prompt-only range near 20-25% to 95.11% on the Paper 09 dev split.

The remaining weakness is not general intent planning; it is temporal-window
grounding. The next model improvement should target dataset-specific temporal
range reasoning rather than more generic training iterations.

## Test Protocol

The Paper 09 test split was not evaluated in this long-run step. Keep it clean
until the method, checkpoint selection rule, and hard-negative protocol are
frozen.

