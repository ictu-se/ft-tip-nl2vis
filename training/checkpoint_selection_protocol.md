# Paper 09 Freeze And Final-Test Protocol

Updated: 2026-06-21

## Purpose

This protocol records the development-only method selection that was frozen
before the final Paper 09 expanded-test evaluation.

The expanded test split was evaluated exactly once after this freeze. Do not
change the method based on the test result.

## Development-Selected Policy

The current dev-selected method is:

```text
metadata-aware planner
  -> learned answerability gate
  -> temporal-support constraint
  -> symmetric-order hard-negative ranker/verifier with fallback
```

The temporal-support constraint is deterministic validation, not the main
learned contribution. The learned model components are the planner, gate, and
ranker.

## Frozen Candidate Components

| Component | Path / Rule | Dev evidence |
| --- | --- | --- |
| Planner | `training/adapters/qwen25_15b_expanded_metadata_smoke/adapters.safetensors` | Best planner tradeoff: 84.22% full-intent and 93.09% temporal-filter; unsupported handled by gate |
| Gate | `training/adapters/qwen25_15b_gate_balanced_smoke/adapters.safetensors` | 99.17% answerability, 0.83% false plot, 0.00% over-refusal |
| Temporal constraint | `scripts/evaluate_temporal_constrained_policy.py` | Repairs exactly 2 malformed dev boundary outputs; no answerability change |
| Ranker | `training/adapters/qwen25_15b_ranker_hard_negative_smoke/adapters.safetensors` | 98.49% original, 98.48% swapped pairwise accuracy |
| Symmetric ranker rule | `scripts/evaluate_symmetric_ranker_policy.py` | 96.97% pair-level consistent/correct; 3.03% fallback |

## Selection Rule

The final method is selected by development evidence only:

1. Use the metadata-aware planner rather than schema-only planner because it
   improves full-dev temporal-filter accuracy from 82.10% to 93.09%.
2. Use the learned gate rather than unsupported-x4 planner because it preserves
   low false plotting without the 12.91% over-refusal introduced by
   unsupported-x4.
3. Use the temporal-support constraint because it repairs malformed temporal
   boundary strings without changing answerability behavior.
4. Use the hard-negative ranker because it distinguishes gold intents from
   plausible temporal hard negatives at 98.49% original and 98.48% swapped
   pairwise accuracy.
5. Use symmetric-order ranker verification because the ranker is strong but not
   perfectly position-invariant; 3.03% of dev pairs are order-sensitive.

## Frozen Scripts

- Planner inference:
  `scripts/run_mlx_intent_inference.py`
- Gate inference:
  `scripts/run_mlx_gate_inference.py`
- Planner+gate composition:
  `scripts/evaluate_composed_policy.py`
- Temporal-constrained policy:
  `scripts/evaluate_temporal_constrained_policy.py`
- Ranker inference:
  `scripts/run_mlx_ranker_inference.py`
- Swapped-order ranker construction:
  `scripts/build_swapped_ranker_eval.py`
- Ranker position-bias analysis:
  `scripts/analyze_ranker_position_bias.py`
- Symmetric ranker policy:
  `scripts/evaluate_symmetric_ranker_policy.py`

## Frozen Metrics

Primary:

- JSON validity;
- answerability accuracy;
- core-intent accuracy;
- full-intent accuracy;
- temporal-filter accuracy;
- required-field F1;
- false-plot rate;
- over-refusal rate;
- hard-negative pairwise accuracy;
- symmetric-ranker consistency/fallback rate.

Slice metrics:

- language;
- task type;
- temporal-support bucket;
- answerability;
- domain/source;
- candidate-position sensitivity.

## Test Set Rule

The final Paper 09 expanded test split was not run until:

1. this file is treated as frozen;
2. the exact command lines for each final test step are written down;
3. the manuscript states that all selection was done on dev;
4. no further dev-driven architecture changes are planned.

After the one-time test run, do not change the method based on the test result.
Only report the result and analyze failures.
