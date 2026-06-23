# Paper 09 Experiment Plan

Updated: 2026-06-21

## Experimental Philosophy

The experiment is the final step to test the mathematical and modeling claim.
The paper should first define the latent intent model, the fine-tuning
objective, and the expected failure modes. Experiments then test whether the
model behaves according to that argument.

The core claim is:

```text
Trustworthy temporal-statistical NL2Vis requires structured intent inference
with explicit temporal support, a learned answerability gate, and a learned
hard-negative ranker/verifier.
```

Deterministic code is allowed only for infrastructure: corpus construction,
metadata extraction, JSON parsing, metric computation, policy composition,
temporal-support validation, and reproducible reporting. The substantive
ambiguity, answerability, and hard-negative discrimination components are model
components.

## Current Data State

| Split | Intent records | Datasets | Ranking pairs |
| --- | ---: | ---: | ---: |
| Train | 14,773 | 547 | 42,152 |
| Dev | 3,269 | 121 | 9,338 |
| Test | 3,111 | 115 | 8,850 |

The expanded test split was evaluated exactly once after the development
protocol was frozen. Do not change the method based on the test result.

## Research Questions

RQ1. Does intent-level fine-tuning improve temporal-statistical intent
faithfulness beyond prompt-only generation?

RQ2. Is temporal-support metadata necessary in practice, or can a schema-only
fine-tuned model infer dataset-specific temporal boundaries?

RQ3. Does a learned answerability gate reduce false plotting without causing
unacceptable over-refusal?

RQ4. Does unsupported oversampling solve false plotting by itself, or does it
trade false plotting for over-refusal and lower intent fidelity?

RQ5. Does a learned hard-negative ranker distinguish correct temporal intents
from schema-plausible but wrong alternatives?

RQ6. Does a narrow temporal-support constraint repair malformed temporal
strings without changing the learned answerability behavior?

RQ7. Are the observed failure modes stable across language, task type, temporal
support range, domain, and model family?

## Completed Dev Evidence

### Full-Dev Architecture Rows

| Variant | Dev n | Core | Full | Answer. | Temporal filter | False plot | Over-refuse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prompt-only Qwen | 3,269 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Schema-only planner | 3,269 | 72.65 | 72.62 | 85.19 | 82.10 | 14.81 | 0.00 |
| Metadata planner | 3,269 | 84.37 | 84.22 | 85.19 | 93.09 | 14.81 | 0.00 |
| Unsupported-x4 planner | 3,269 | 79.63 | 79.23 | 86.85 | 85.81 | 0.24 | 12.91 |
| Metadata planner + gate | 3,269 | 88.10 | 87.95 | 99.17 | 93.09 | 0.83 | 0.00 |
| Planner + gate + temporal constraint | 3,269 | 88.16 | 88.01 | 99.17 | 93.15 | 0.83 | 0.00 |

### Ranker Evidence

| Metric | Value |
| --- | ---: |
| Train ranking pairs | 42,152 |
| Dev ranking pairs | 9,338 |
| JSON validity | 100.00 |
| Pairwise accuracy | 98.49 |
| Accuracy when gold is A | 96.95 |
| Accuracy when gold is B | 100.00 |

### Temporal Candidate Subset

On the 1,573 development samples with temporal hard-negative candidate sets:

| Metric | Planner+Gate+Temporal Constraint |
| --- | ---: |
| Core accuracy | 98.92 |
| Full accuracy | 98.79 |
| Temporal-filter accuracy | 100.00 |
| Temporal-filter failures | 0 |
| Ranker sample majority-gold verification | 99.68 |

## Pre-Test Work Status

1. **Anti-position-bias ranker ablation**
   - Train or evaluate a symmetric ranker setting that balances/duplicates
     candidate order.
   - Completed with original, swapped, paired position-bias, and symmetric-order
     policy analyses.

2. **Planner+gate+ranker decision policy**
   - Convert ranker evidence from pairwise verification into an explicit policy
     row.
   - Completed as the frozen planner--gate--temporal-constraint policy plus
     symmetric-order ranker verifier/fallback analysis.

3. **Cross-family prompt-only table cleanup**
   - Current dev64 prompt-only baselines cover Qwen, Qwen-Coder, Llama, Gemma,
     Mistral, Mixtral, Phi, and DeepSeek-Coder.
   - Mistral-7B and Mixtral-8x7B were pulled locally and added as prompt-only
     smoke rows.
   - Do not run full prompt-only baselines for families already showing
     systematic non-compliance unless the result would change the conclusion.

4. **Slice analysis finalization**
   - Language: English vs Vietnamese.
   - Task type: temporal windows, rankings, change tasks, unsupported requests.
   - Temporal support: old-ending vs recent-ending datasets.
   - Completed for final-test task/failure slices; human-audit examples remain
     to be added before submission.

5. **Checkpoint and script freeze**
   - Record exact adapter paths.
   - Record exact inference scripts and command lines.
   - Record checkpoint-selection rule.
   - Completed before the one-time final test run.

6. **Final expanded test**
   - Completed once at 2026-06-20 23:42 +07.
   - Final method must remain frozen after this result.

7. **Adapter rank/layer coverage ablation**
   - Completed dev64 screening for rank 4, rank 8, rank 16, rank 32, last-8,
     last-16, and all-layer metadata-aware LoRA planners.
   - Completed full-dev confirmation for `rank8_all_layers` and `rank16_l16`.
   - Added the result table and interpretation to the manuscript.

## Required Final Tables

1. Expanded corpus statistics.
2. Cross-family prompt-only baselines.
3. Representation ablation: schema-only vs metadata-aware.
4. Objective/architecture ablation:
   - metadata planner;
   - unsupported-x4 planner;
   - planner + gate;
   - planner + gate + temporal constraint;
   - ranker/verifier.
5. Ranker full-dev and anti-position-bias result.
6. Slice/failure analysis.
7. Final frozen test table, run once only after freeze.
8. Final-test residual failure analysis.
9. Adapter rank/layer coverage ablation table.
10. Statistical reliability table with bootstrap confidence intervals.
11. Paired significance/effect table over matched records.
12. Reproducibility checklist and artifact manifest.

## Test-Set Gate

The expanded test split has already been run once. It was run only after all of
these conditions were true:

- final planner adapter is selected;
- final gate adapter is selected;
- final ranker variant is selected;
- temporal-support constraint behavior is frozen;
- exact inference scripts and command lines are frozen;
- final ablation rows are fixed;
- manuscript states the dev-only selection rule.

After the one-time test run, do not change the method based on the test result.

## Stop Criteria

Do not keep running full baselines mechanically if interim results show:

- formatting degeneration;
- no meaningful improvement over prompt-only baseline;
- systematic over-refusal;
- obvious saturation;
- a conclusion that is already stable across families or slices.

Continue only when the additional run changes the scientific conclusion.

## Remaining Optional Dissertation-Strength Work

The minimal publishable experiment set is complete, and the main
dissertation-strength adapter-capacity ablation is also complete. The optional
multilingual/external audit pass is now also complete:

- Mistral-7B prompt-only dev64 smoke: 100.00% JSON, 0.00% core/full intent.
- Mixtral-8x7B prompt-only dev64 smoke: 100.00% JSON, 0.00% core/full intent.
- Vietnamese diacritic planner audit: n=1,332, 81.68% core, 72.60% full,
  99.47% temporal-filter accuracy.
- Non-World-Bank planner audit: n=56, 82.14% core, 76.79% full,
  94.64% temporal-filter accuracy.
- Dissertation-rigor statistical package is complete:
  - 28 bootstrap confidence-interval rows;
  - 20 paired McNemar-style tests;
  - 37 final-test slice rows;
  - 30 optional-audit slice rows;
  - 19 final-test task-confusion rows;
  - reproducibility file check with no missing required artifacts.

Remaining optional work:

1. Add human-audit examples for `mixed_change_ranking`, unsupported monthly
   granularity, future forecast, and unavailable city-level requests.
