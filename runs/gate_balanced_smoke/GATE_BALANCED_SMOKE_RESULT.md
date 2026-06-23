# Gate-Balanced Smoke Result

This run trains the first explicit answerability-gate component for the Paper 09
planner--gate--ranker architecture. It uses only expanded train/dev splits; the
expanded test split remains untouched.

## Training

- Model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- Adapter: `training/adapters/qwen25_15b_gate_balanced_smoke/`
- Training data: `training/gate_ranker_artifacts/gate_train_balanced.jsonl`
- Validation data: `training/gate_ranker_artifacts/gate_dev.jsonl`
- Iterations: 300
- Prompt masking: enabled
- Validation loss: 2.380 -> 0.019 -> 0.010 -> 0.001
- Peak memory: 2.541 GB

## Full Expanded-Dev Gate Evaluation

| Metric | Value |
| --- | ---: |
| Dev records | 3,269 |
| JSON validity | 100.00% |
| Answerability accuracy | 99.17% |
| False-plot rate over all dev | 0.83% |
| False-plot rate among unanswerable requests | 5.58% |
| Over-refusal rate over all dev | 0.00% |
| Over-refusal rate among answerable requests | 0.00% |

## Comparison Against Planner-Only Rows

| Variant | Answerability accuracy | False-plot rate | Over-refusal rate |
| --- | ---: | ---: | ---: |
| Metadata LoRA planner | 85.19% | 14.81% | 0.00% |
| Unsupported-x4 planner | 86.85% | 0.24% | 12.91% |
| Gate-balanced adapter | 99.17% | 0.83% | 0.00% |

## Interpretation

The gate-balanced adapter gives the missing safety behavior that the
metadata-aware planner lacked, while avoiding the over-refusal pathology of the
unsupported-x4 planner. This is the first strong evidence that Paper 09 should
use a separate answerability gate rather than trying to force unsupported
behavior entirely through planner SFT.

The remaining modeling task is to combine:

```text
metadata-aware planner + gate-balanced answerability gate + hard-negative ranker
```

and evaluate the combined decision policy on full expanded dev before touching
the expanded test split.
