# Rigorous Ablation Protocol

## Why This Is Needed

The current Paper 09 result is now beyond a LoRA-only proof of direction: it
contains full-dev planner, gate, temporal-constraint, ranker evidence, and a
single frozen expanded-test evaluation. The remaining purpose of this protocol
is to distinguish the completed minimal publishable ablations from optional
dissertation-strength extensions.

The final paper should therefore treat each component as one row in a larger
ablation study: schema-only planner, metadata-aware planner, unsupported-x4
planner, learned gate, temporal-support constraint, and learned ranker.

## Core Model Claim To Test

The final method claim should be:

```text
Temporal-statistical intent faithfulness improves when the model is trained not
only to imitate JSON labels, but also to distinguish valid temporal-grounded
intents from hard negative intents that preserve surface schema validity while
violating temporal/statistical commitments.
```

This means the final method must include model-level additions beyond plain SFT:

- hard-negative contrastive/ranking objective;
- temporal-window grounding supervision;
- planner-plus-ranker/verifier;
- answerability gate or unsupported-intent objective;
- adapter placement/rank ablation;
- metadata-aware schema serialization ablation.

The doctoral-core objective is:

```text
L_core = L_SFT + beta L_rank + gamma L_boundary + rho L_gate
```

The paper must show which term matters. A result table that only says "LoRA is
better than prompting" is not enough for the thesis-level core paper.

## Required Ablation Groups

## Expanded Corpus Baseline

The serious Paper 09 setting now uses the expanded local corpus:

| Quantity | Value |
| --- | ---: |
| CSV-backed datasets | 783 |
| Intent records | 21,153 |
| Train records | 14,773 |
| Dev records | 3,269 |
| Test records | 3,111 |
| Temporal hard-negative ranking pairs | 60,340 |

The expanded metadata-aware smoke run was viable and led to the full-dev
architecture rows now used in the manuscript. Its main failure mode was false
plotting of unsupported monthly-granularity requests. The learned answerability
gate fixes this more cleanly than unsupported oversampling.

## Current Full-Dev Rows

| Variant | Core | Full | Answer. | Temp. filter | False plot | Over-refuse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prompt-only Qwen | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Schema-only planner | 72.65 | 72.62 | 85.19 | 82.10 | 14.81 | 0.00 |
| Metadata planner | 84.37 | 84.22 | 85.19 | 93.09 | 14.81 | 0.00 |
| Unsupported-x4 planner | 79.63 | 79.23 | 86.85 | 85.81 | 0.24 | 12.91 |
| Metadata planner + gate | 88.10 | 87.95 | 99.17 | 93.09 | 0.83 | 0.00 |
| Planner + gate + temporal constraint | 88.16 | 88.01 | 99.17 | 93.15 | 0.83 | 0.00 |

The hard-negative ranker reaches 98.49% pairwise accuracy on all 9,338
development ranking pairs, with 96.95% accuracy when the gold candidate is A
and 100.00% when the gold candidate is B.

### A. Model And Prompt Baselines

| ID | Variant | Purpose |
| --- | --- | --- |
| A0 | Prompt-only base Qwen2.5-1.5B | Completed full-dev; measures base model without fine-tuning. |
| A1 | Prompt-only larger Qwen/Qwen-Coder | Completed dev64 for Qwen2.5-3B, Qwen2.5-Coder-7B, and Qwen3-4B. |
| A2 | Prompt-only non-Qwen family | Dev64 completed for Llama3.2-3B, Mistral-7B, Mixtral-8x7B, Gemma, Phi, and DeepSeek-Coder. |
| A3 | Paper 08 best prompt-only baseline | Historical comparison. |

### B. Fine-Tuning Objective Ablations

| ID | Variant | Purpose |
| --- | --- | --- |
| B0 | SFT-only LoRA | Completed for schema-only and metadata-aware planners. |
| B1 | SFT + hard-negative ranking | Completed as a learned pairwise ranker with anti-position-bias and symmetric-order analyses. |
| B2 | SFT + temporal-window auxiliary targets | Tests dataset-specific temporal grounding. |
| B3 | SFT + ranking + temporal-window targets | Candidate final method. |
| B4 | Answerable-only SFT | Completed dev64; preserves full-intent on the slice but weakens temporal-filter accuracy. |
| B5 | No prompt masking | Completed dev64; substantially weakens full-intent accuracy. |
| B6 | Learned answerability gate | Completed; tests separate unsupported-intent decision boundary. |
| B7 | Temporal-support constraint | Completed; tests malformed temporal-filter repair as validation, not core learning. |

### C. Adapter Architecture Ablations

| ID | Variant | Purpose |
| --- | --- | --- |
| C0 | LoRA rank 4 | Completed dev64; under-parameterized for temporal grounding. |
| C1 | LoRA rank 8 | Completed as current default and all-layer variant. |
| C2 | LoRA rank 16 | Completed dev64 and full-dev follow-up. |
| C3 | LoRA rank 32 | Completed dev64; did not beat rank 16. |
| C4 | Last 8 layers only | Completed dev64; substantially weaker. |
| C5 | Last 16 layers | Completed as current default and rank variants. |
| C6 | All layers | Completed dev64 and full-dev follow-up; strongest temporal-filter/answerability behavior. |

### D. Data Representation Ablations

| ID | Variant | Purpose |
| --- | --- | --- |
| D0 | Schema fields only | Current simple schema serialization. |
| D1 | Schema + dataset temporal min/max | Tests temporal range grounding. |
| D2 | Schema + candidate temporal windows | Tests explicit candidate-space conditioning. |
| D3 | English-only training | Completed dev64; weakens mixed-language full-intent and temporal-filter accuracy. |
| D4 | Bilingual training | Current/default. |
| D5 | Vietnamese diacritic audit split | Completed on 1,332 dev records; tests realistic Vietnamese robustness. |

### F. Unsupported-Intent And Hard-Negative Ablations

| ID | Variant | Purpose |
| --- | --- | --- |
| F0 | Metadata-aware SFT only | Completed full-dev. |
| F1 | Metadata-aware SFT with oversampled unsupported requests | Completed full-dev; reduces false plot but causes over-refusal. |
| F2 | Metadata-aware SFT with temporal-window hard negatives serialized as rejected candidates | Tests temporal boundary discrimination. |
| F3 | Planner plus learned ranker over positive/negative intent pairs | Completed full-dev pairwise with anti-position-bias control. |
| F4 | Unsupported-only auxiliary classifier head or verifier | Completed as learned gate. |
| F5 | Planner + gate + temporal-support constraint | Completed full-dev; repairs malformed temporal filters without changing answerability. |

### G. Analysis Slice Ablations

| ID | Slice | Purpose |
| --- | --- | --- |
| G0 | Datasets ending in 2010 or earlier | Tests whether the model memorizes modern default windows. |
| G1 | Datasets ending in 2023--2025 | Tests recent-data temporal grounding. |
| G2 | Monthly unsupported requests | Tests false plotting under unavailable granularity. |
| G3 | Future forecast requests | Tests unsupported statistic detection. |
| G4 | City/dimension unavailable requests | Tests field and dimension grounding. |
| G5 | Vietnamese prompts | Tests multilingual transfer. |
| G6 | Multi-measure derived datasets | Tests secondary-measure and correlation behavior. |

### E. Checkpoint And Generalization

| ID | Variant | Purpose |
| --- | --- | --- |
| E0 | Checkpoint 200 | Early fit. |
| E1 | Checkpoint 400 | Mid fit. |
| E2 | Checkpoint 600 | Possible loss rebound. |
| E3 | Checkpoint 800 | Low validation loss. |
| E4 | Checkpoint 1000 | Current final adapter. |

## Required Metrics

Primary:

- core-intent accuracy;
- full-intent accuracy;
- temporal-filter accuracy;
- task-type accuracy;
- statistic accuracy;
- required-field F1;
- false-plot unanswerable rate;
- over-refusal rate.

Secondary:

- JSON validity;
- validation loss;
- per-language scores;
- per-task-type scores;
- temporal-window exact match;
- temporal-window boundary error in years, when applicable.
- bootstrap confidence intervals for headline accuracies;
- paired McNemar-style tests for matched-record comparisons.

## Minimal Publishable Ablation Set

The current minimum rigorous set is:

1. prompt-only base Qwen2.5-1.5B;
2. prompt-only non-Qwen family baseline;
3. expanded schema-only LoRA;
4. expanded temporal-metadata-aware LoRA;
5. metadata-aware LoRA with unsupported-request oversampling;
6. learned answerability gate;
7. planner + gate composed policy;
8. temporal-support constrained policy;
9. learned hard-negative ranker/verifier;
10. anti-position-bias ranker control;
11. final frozen test row.

LoRA rank 4 vs 8 vs 16 vs 32 and layer-depth ablations have now been completed
as dissertation-strength additions. The optional Mistral/Mixtral prompt-only smoke,
Vietnamese diacritic audit, and non-World-Bank validation slice are also
complete. The statistical/reproducibility package is also complete, including
bootstrap confidence intervals, paired tests, final-test slice matrices,
optional-audit slice matrices, task-confusion tables, reproducibility checks,
and generated manuscript figures. Remaining optional extensions are human-audit
examples.

## Optional Robustness/External Audits

| Audit | n | Core | Full | Answer. | Temp. filter | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Mistral-7B prompt-only dev64 | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 100.00% JSON, same prompt-only failure pattern. |
| Mixtral-8x7B prompt-only dev64 | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 100.00% JSON, same prompt-only failure pattern despite much larger MoE model. |
| Vietnamese diacritic planner audit | 1,332 | 81.68 | 72.60 | 81.83 | 99.47 | Temporal support remains robust; full-intent drops under surface-form variation. |
| Non-World-Bank planner audit | 56 | 82.14 | 76.79 | 85.71 | 94.64 | OWID/derived-source stress test; external schema coverage remains weaker. |

## Statistical And Reproducibility Artifacts

| Artifact | Status |
| --- | --- |
| Bootstrap confidence intervals | Complete: `runs/dissertation_rigor_20260621/bootstrap_metric_ci.csv`. |
| Paired McNemar-style tests | Complete: `runs/dissertation_rigor_20260621/paired_mcnemar_tests.csv`. |
| Final-test slice matrix | Complete: `runs/dissertation_rigor_20260621/final_test_slice_matrix.csv`. |
| Optional-audit slice matrix | Complete: `runs/dissertation_rigor_20260621/optional_audit_slice_matrix.csv`. |
| Task-confusion table | Complete: `runs/dissertation_rigor_20260621/final_test_task_confusions.csv`. |
| Reproducibility checklist | Complete: `REPRODUCIBILITY.md`, no missing required artifacts. |

## Test-Set Rule

The final expanded-test evaluation has already been run once after:

1. the final method variant is selected using dev only;
2. ablation rows are frozen;
3. the exact checkpoint-selection rule is frozen;
4. the exact inference/evaluation script is frozen.
5. the anti-position-bias decision for the ranker is complete.

Do not change the method based on the final test result.
