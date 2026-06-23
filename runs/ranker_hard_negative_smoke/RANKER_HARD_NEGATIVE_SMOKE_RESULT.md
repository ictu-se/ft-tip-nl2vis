# Hard-Negative Ranker Smoke Result

This run trains the first explicit pairwise intent ranker for Paper 09. The
ranker chooses between a gold temporal intent and a schema-plausible hard
negative whose temporal window is wrong.

The expanded test split remains untouched.

## Training

- Model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- Adapter: `training/adapters/qwen25_15b_ranker_hard_negative_smoke/`
- Train data: `training/gate_ranker_artifacts/ranker_train.jsonl`
- Dev data: `training/gate_ranker_artifacts/ranker_dev.jsonl`
- Train pairs: 42,152
- Dev pairs: 9,338
- Iterations: 300
- Prompt masking: enabled
- Validation loss: 3.608 -> 0.001 -> 0.000 -> 0.000
- Peak memory: 3.540 GB

## Dev1024 Pairwise Inference

| Metric | Value |
| --- | ---: |
| Evaluated dev pairs | 1,024 |
| JSON validity | 100.00% |
| Pairwise accuracy | 96.09% |
| Accuracy when gold is A | 91.75% |
| Accuracy when gold is B | 100.00% |

## Error Pattern

The 40 observed errors all occur when the gold positive candidate is A but the
ranker predicts B. This suggests a mild positional bias toward B after the
smoke run. The next ranker experiment should either:

- run full dev to confirm whether the bias persists;
- increase candidate-order balancing or add an explicit anti-position-bias
  check;
- train the ranker longer only if full-dev pairwise accuracy is still below the
  desired threshold.

## Interpretation

The ranker successfully learns to distinguish correct temporal windows from
hard negatives on a substantial dev slice. Together with the gate result, this
turns Paper 09 from a LoRA-only planner into an implemented planner--gate--ranker
architecture:

```text
metadata-aware planner + answerability gate + hard-negative ranker
```

The next scientific step is to evaluate the ranker on all 9,338 dev pairs and
then integrate it into the composed policy for candidate selection.
