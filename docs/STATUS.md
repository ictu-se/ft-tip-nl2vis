# Paper 09 Status

Created: 2026-06-19

## Done

- Created Paper 09 folder structure.
- Defined working title and thesis.
- Drafted mathematical model and latent-intent formulation.
- Drafted fine-tuning plan.
- Drafted experiment plan.
- Drafted manuscript outline.
- Built deterministic train/dev/test split from Paper 08 TimeStat-NL2Vis.
- Built SFT-format instruction records.
- Recorded local model/toolchain setup notes.
- Installed Homebrew Python 3.11 for fine-tuning.
- Created dedicated `.venv` for Paper 09.
- Installed and verified MLX-LM fine-tuning stack.
- Linked SFT data into MLX-LM `train/valid/test.jsonl` layout.
- Completed first smoke LoRA fine-tune with `mlx-community/Qwen2.5-1.5B-Instruct-4bit`.
- Saved smoke adapter and logs under `runs/smoke_qwen25_15b_lora/`.
- Verified one qualitative test case where the adapter exactly matched the gold intent JSON.
- Added `scripts/run_mlx_intent_inference.py` for batched MLX adapter inference and structured metrics.
- Evaluated the smoke adapter on the full dev split: 61.41% core-intent accuracy and 57.07% full-intent accuracy.
- Completed a 1000-iteration Qwen2.5 1.5B LoRA run.
- Evaluated the long adapter on the full dev split: 95.11% core-intent accuracy and 95.11% full-intent accuracy.
- Saved long-run report and residual dev failures under `runs/long_qwen25_15b_lora/`.
- Drafted the first LaTeX working manuscript under `draft/`.
- Compiled `draft/main.pdf` and copied it to `Paper09_FT_TIP_working_manuscript.pdf`.
- Revised the manuscript to be more method-heavy: adapterized planner, temporal-boundary formulation, hard-negative ranking objective, total objective, and rigorous ablation protocol.
- Added `training/ablation_protocol.md`.
- Recompiled the revised 9-page working PDF.
- Built an expanded Paper 09 corpus from all local benchmark metadata and CSV files.
- Verified 783/783 metadata datasets are usable for temporal-statistical intent generation.
- Generated 21,153 expanded intent records and 60,340 temporal hard-negative ranking pairs.
- Created grouped expanded train/dev/test splits by `dataset_id`, stratified by domain and temporal recency bucket.
- Added `scripts/build_expanded_timestat_corpus.py`.
- Ran a 300-iteration expanded metadata-aware Qwen2.5-1.5B LoRA smoke run.
- Saved expanded metadata adapter under `training/adapters/qwen25_15b_expanded_metadata_smoke/`.
- Structured dev64 smoke result: 100% JSON validity, 87.50% core-intent accuracy, 85.94% full-intent accuracy.
- Identified the next major modeling weakness: unsupported monthly-granularity requests are still often answered instead of refused.
- Updated `scripts/run_mlx_intent_inference.py` with checkpointed JSONL output and `--resume` support for long full-dev evaluations.
- Reframed Paper 09 as the doctoral-core model paper rather than a LoRA-only result.
- Added planner--gate--ranker architecture to the manuscript.
- Added mathematical sections for intent-space safety risk, false plotting, over-refusal, temporal-support ambiguity, risk decomposition, temporal-support encoding, and unsupported-intent objective.
- Added the doctoral-core objective: `L_core = L_SFT + beta L_rank + gamma L_boundary + rho L_gate`.
- Added `notes/doctoral_core_model_and_experiment_matrix.md` with the thesis-level model and experiment matrix.
- Expanded `experiment_plan.md` and `training/ablation_protocol.md` to require multi-angle evaluation: model family, representation, objective, adapter architecture, data domain, language, safety, and failure-mode slices.
- Recompiled the working manuscript PDF; current compiled version is 12 pages.
- Ran expanded schema-only Qwen2.5-1.5B LoRA smoke as the first direct representation ablation.
- Schema-only 300-iteration smoke: validation loss 2.181 -> 0.018, peak memory 2.756 GB.
- Schema-only dev64: 100% JSON validity, 62.50% core-intent accuracy, 62.50% full-intent accuracy, 68.75% temporal-filter accuracy.
- Compared with temporal-metadata dev64: 87.50% core-intent accuracy, 85.94% full-intent accuracy, 96.875% temporal-filter accuracy.
- Added `runs/expanded_schema_smoke/EXPANDED_SCHEMA_SMOKE_RESULT.md`.
- Added the schema-only vs temporal-metadata ablation table to the manuscript.
- Expanded the working manuscript with a doctoral-core experimental design section; current compiled version is 16 pages.
- Built unsupported-x4 oversampled metadata-aware training data: 21,337 records with unsupported exposure increased to 41.02%.
- Ran unsupported-x4 300-iteration Qwen2.5-1.5B LoRA smoke.
- Unsupported-x4 dev64: answerability accuracy 100.00%, core-intent 87.50%, full-intent 87.50%, temporal-filter accuracy 92.1875%.
- Compared with metadata SFT dev64: answerability improves 87.50% -> 100.00%, full-intent improves 85.94% -> 87.50%, but temporal-filter drops 96.875% -> 92.1875%.
- Added `runs/expanded_metadata_unsupported_x4_smoke/UNSUPPORTED_X4_SMOKE_RESULT.md`.
- Added unsupported-x4 ablation table to the manuscript.
- Added `scripts/run_ollama_intent_inference.py` for local Ollama prompt-only cross-family baselines.
- Ran prompt-only Qwen2.5-1.5B baseline on expanded dev64: 100% JSON validity but 0% core/full intent accuracy.
- Ran prompt-only Gemma3-4B baseline on expanded dev64: 100% JSON validity but 0% core/full intent accuracy.
- Ran prompt-only Phi3-mini baseline on expanded dev64: 93.75% JSON validity and 0% core/full intent accuracy.
- Ran prompt-only DeepSeek-Coder-6.7B baseline on expanded dev64: 100% JSON validity and 0% core/full intent accuracy.
- Added `runs/PROMPT_BASELINES_DEV64_RESULT.md`.
- Expanded prompt-only baseline table in the manuscript to four model families: Qwen, Gemma, Phi, and DeepSeek-Coder.
- Recompiled the working manuscript PDF; current compiled version is 17 pages.
- Completed overnight full expanded-dev evaluation for metadata LoRA, unsupported-x4 LoRA, schema-only LoRA, and Qwen prompt-only.
- Added `scripts/analyze_full_dev_errors.py`.
- Generated full-dev error analysis under `runs/overnight_full_dev_20260619/error_analysis/`.
- Full-dev confirms metadata LoRA is currently the best planner: 84.37% core-intent, 84.22% full-intent, 93.09% temporal-filter.
- Metadata LoRA is nearly perfect on answerable dev records but fails on unsupported requests: 14.81% false-plot rate and 0.00% over-refusal.
- Unsupported-x4 reduces false plotting but creates 12.91% over-refusal and drops full-intent to 79.23%.
- Added `scripts/build_gate_ranker_artifacts.py`.
- Built gate/ranker train-dev artifacts under `training/gate_ranker_artifacts/`: gate train 14,773, balanced gate train 4,376, ranker train 42,152 pairs, ranker dev 9,338 pairs.
- Added `scripts/run_mlx_gate_inference.py`.
- Trained first explicit gate adapter: `training/adapters/qwen25_15b_gate_balanced_smoke/`.
- Gate-balanced 300-iteration smoke: validation loss 2.380 -> 0.001.
- Gate-balanced full expanded-dev: 100.00% JSON validity, 99.17% answerability accuracy, 0.83% false-plot rate, 0.00% over-refusal.
- Added `runs/gate_balanced_smoke/GATE_BALANCED_SMOKE_RESULT.md`.
- Added `scripts/evaluate_composed_policy.py`.
- Composed metadata planner + gate on full expanded-dev: 88.10% core-intent, 87.95% full-intent, 99.17% answerability, 0.83% false-plot, 0.00% over-refusal.
- Added `runs/gate_balanced_smoke/COMPOSED_PLANNER_GATE_RESULT.md`.
- Trained first hard-negative pairwise ranker: `training/adapters/qwen25_15b_ranker_hard_negative_smoke/`.
- Ranker 300-iteration smoke: validation loss 3.608 -> 0.000.
- Added `scripts/run_mlx_ranker_inference.py`.
- Ranker dev1024 inference: 100.00% JSON validity and 96.09% pairwise accuracy.
- Added `runs/ranker_hard_negative_smoke/RANKER_HARD_NEGATIVE_SMOKE_RESULT.md`.
- Added `notes/doctoral_core_execution_plan.md` to define the remaining doctoral-core execution path and test-set gate.
- Added `scripts/evaluate_composed_policy.py` results to the manuscript.
- Updated `draft/main.tex` with the full-dev architecture table, answerability-gate result, and ranker smoke result.
- Recompiled `draft/main.pdf`; copied the current working PDF to `Paper09_FT_TIP_working_manuscript.pdf`.
- Completed full 9,338-pair ranker dev inference: 100.00% JSON validity and 98.49% pairwise accuracy.
- Full ranker dev split result: 96.95% accuracy when gold is A and 100.00% accuracy when gold is B.
- Updated `draft/main.tex` with the full-dev ranker result and removed the obsolete full-ranker-next-step language.
- Recompiled `draft/main.pdf`; copied the updated working PDF to `Paper09_FT_TIP_working_manuscript.pdf`.
- Added `scripts/analyze_ranker_policy_integration.py`.
- Ranker policy-integration analysis: 1,573 temporal-policy samples, 99.68% sample-level majority-gold verification, 92.37% all-negatives-rejected verification, and only 2 planner+gate temporal-filter failures.
- The two remaining temporal-filter failures are malformed range outputs (`1-12-2003-2019` and `1-12`), not existing constructed hard negatives, so the next method step should add candidate generation or constrained temporal-range normalization before ranker selection.
- Added `scripts/evaluate_temporal_constrained_policy.py`.
- Temporal-constrained planner+gate full-dev result: 88.16% core-intent, 88.01% full-intent, 93.15% temporal-filter accuracy, 99.17% answerability, 0.83% false plotting, and 0.00% over-refusal.
- The temporal constraint repaired exactly 2 malformed boundary outputs and leaves answerability behavior unchanged.
- On the 1,573 temporal-candidate development samples, the temporal-constrained policy reaches 100.00% temporal-filter accuracy.
- Added `runs/gate_balanced_smoke/TEMPORAL_CONSTRAINED_POLICY_RESULT.md`.
- Audited and updated `experiment_plan.md`, `training/ablation_protocol.md`, and `notes/doctoral_core_execution_plan.md` to match the current full-dev planner, gate, temporal-constraint, and ranker evidence.
- Added `scripts/build_swapped_ranker_eval.py` for anti-position-bias ranker evaluation.
- Built `training/gate_ranker_artifacts/ranker_dev_swapped.jsonl` with all 9,338 dev ranking pairs in reversed candidate order.
- Swapped-ranker dev128 smoke: 100.00% JSON validity, 92.97% pairwise accuracy, 87.14% accuracy when gold is A, and 100.00% accuracy when gold is B.
- Started full swapped-order ranker dev inference in detached screen session `paper09_ranker_swapped_full`, with `paper09_ranker_swapped_caffeinate` keeping the machine awake.
- Added `scripts/analyze_ranker_position_bias.py` to compare original and swapped ranker outputs after the full swapped run completes.
- Completed full swapped-order ranker dev inference: 100.00% JSON validity and 98.48% pairwise accuracy.
- Swapped full-dev split result: 96.99% accuracy when gold is A and 100.00% accuracy when gold is B.
- Position-bias paired analysis: 96.97% both orders correct, 3.03% order-sensitive, 1.52% original-only correct, 1.51% swapped-only correct, and 0.00% both-wrong.
- Order sensitivity is concentrated in `mixed_change_ranking` at 18.46%; direct temporal-window tasks are much more stable.
- Added `runs/ranker_hard_negative_smoke/RANKER_POSITION_BIAS_RESULT.md`.
- Updated `draft/main.tex` with the anti-position-bias ranker result and revised the next-step language.
- Added `scripts/evaluate_symmetric_ranker_policy.py`.
- Symmetric-order ranker policy: 96.97% pair-level consistent/correct decisions, 3.03% order-sensitive fallback decisions, 98.54% sample-level majority-correct decisions, and 87.54% sample-level all-pairs-correct decisions over 1,573 temporal-candidate samples.
- Added `runs/ranker_hard_negative_smoke/SYMMETRIC_RANKER_POLICY_RESULT.md`.
- Updated `draft/main.tex` with the symmetric-order ranker policy table and moved the next step to protocol/checkpoint freeze before one-time test evaluation.
- Rewrote `training/checkpoint_selection_protocol.md` as the Paper 09 pre-test freeze protocol, recording the dev-selected planner, gate, temporal-support constraint, symmetric ranker rule, adapter paths, scripts, and frozen metrics.
- Recompiled `draft/main.pdf` and copied the updated 20-page PDF to `Paper09_FT_TIP_working_manuscript.pdf`.
- Cleaned up the completed swapped-ranker caffeinate screen session; no experiment screens remain running.
- Added `FINAL_TEST_COMMANDS.md`.
- Added `scripts/build_gate_ranker_test_artifacts.py`.
- Added `scripts/run_final_test_once.sh`.
- Started the frozen final expanded-test run in detached screen session `paper09_final_test`, with `paper09_final_test_caffeinate` keeping the machine awake.
- Built final test gate/ranker artifacts: 3,111 test intent records and 8,850 test hard-negative ranking pairs.
- Completed frozen final expanded-test run at 2026-06-20 23:42 +07.
- Final test planner-only result: 100.00% JSON, 84.02% core-intent, 83.83% full-intent, and 93.67% temporal-filter accuracy.
- Final test gate result: 99.10% answerability, 0.90% false plotting, and 0.00% over-refusal.
- Final test planner+gate+temporal-constraint result: 88.49% core-intent, 88.30% full-intent, 93.73% temporal-filter, 99.10% answerability, 0.90% false plotting, and 0.00% over-refusal.
- Final test ranker result: 98.34% original-order pairwise accuracy and 98.25% swapped-order pairwise accuracy over 8,850 hard-negative pairs.
- Final test symmetric ranker policy: 96.59% pair-level consistent/correct, 3.41% order-sensitive fallback, 98.06% sample-level majority-correct, and 85.75% sample-level all-pairs-correct over 1,495 temporal-candidate test samples.
- Added `runs/final_test_20260620/FINAL_TEST_RESULT.md`.
- Updated `draft/main.tex` with frozen expanded-test intent and ranker tables.
- Added `scripts/analyze_final_test_failures.py`.
- Generated final-test failure analysis under `runs/final_test_20260620/failure_analysis/`.
- Final-test residual taxonomy: wrong task type 11.31%, wrong temporal filter 6.27%, wrong statistic 1.22%, wrong measure 1.00%, false plot 0.90%, wrong time field 0.90%, and core-correct/full-wrong 0.19%.
- Final-test slice analysis identifies `mixed_change_ranking` as the weakest answerable operation slice: 82.61% full-intent accuracy and 19.86% ranker order-sensitive pairs, despite 100.00% temporal-filter accuracy.
- Updated `draft/main.tex` with a frozen-test residual error analysis subsection and failure taxonomy table.

## Data Snapshot

Paper 09 split from 1,200 TimeStat-NL2Vis records:

| Split | n | Datasets | English | Vietnamese | Answerable | Unanswerable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 832 | 37 | 508 | 324 | 688 | 144 |
| dev | 184 | 8 | 112 | 72 | 152 | 32 |
| test | 184 | 8 | 112 | 72 | 152 | 32 |

Expanded Paper 09 split from all local dataset metadata and CSV files:

| Split | n | Datasets | Notes |
| --- | ---: | ---: | --- |
| train | 14,773 | 547 | Covers all 13 domains |
| dev | 3,269 | 121 | Used for checkpoint and ablation selection |
| test | 3,111 | 115 | Clean final holdout; not used |

Expanded hard-negative temporal ranking pairs:

| Split | Pairs |
| --- | ---: |
| train | 42,152 |
| dev | 9,338 |
| test | 8,850 |

## Next Technical Steps

1. Add human-audit examples before submission, especially for `mixed_change_ranking`, unsupported monthly granularity, future forecast, and unavailable city-level requests.
2. Do not change the method based on the final test result.

## Dissertation-Strength Experiment Extension

- Added `scripts/run_dissertation_strength_experiments.sh`.
- Started detached screen session `paper09_dissertation_strength` at 2026-06-21 08:04 +07.
- Started sleep-prevention screen session `paper09_dissertation_strength_caffeinate`.
- Run directory: `runs/dissertation_strength_20260621/`.
- Live log: `runs/dissertation_strength_20260621/run.log`.
- Planned extension run:
  1. prompt-only dev64 baselines for `llama3.2:3b`, `qwen2.5:3b`, `qwen2.5-coder:7b`, and `qwen3:4b`;
  2. metadata-aware LoRA rank ablations: rank 4, rank 16, rank 32 with 16 trained layers;
  3. metadata-aware LoRA layer-depth ablations: rank 8 with last 8 layers and all layers;
  4. dev64 evaluation for each ablation before deciding whether any variant deserves full-dev reporting.
- This extension is dev-only reporting evidence. It must not change the frozen final-test method.
- Completed dissertation-strength dev64 extension:
  - prompt-only `llama3.2:3b`, `qwen2.5:3b`, `qwen2.5-coder:7b`, and `qwen3:4b` all reached 100% JSON validity but 0% core/full intent accuracy on dev64;
  - LoRA `rank4_l16`: 85.94% full-intent and 92.19% temporal-filter accuracy on dev64;
  - LoRA `rank16_l16`: 95.31% full-intent and 96.88% temporal-filter accuracy on dev64;
  - LoRA `rank32_l16`: 93.75% full-intent and 96.88% temporal-filter accuracy on dev64;
  - LoRA `rank8_l8`: 76.56% full-intent and 92.19% temporal-filter accuracy on dev64;
  - LoRA `rank8_all_layers`: 96.88% full-intent, 100.00% temporal-filter, and 100.00% answerability accuracy on dev64.
- Added `scripts/run_full_dev_adapter_ablation_followup.sh`.
- Started full-dev follow-up plan for `rank8_all_layers` and `rank16_l16` to confirm whether the dev64 adapter-capacity result holds on all 3,269 development records.
- Completed full-dev follow-up:
  - LoRA `rank8_all_layers`: 95.50% full-intent, 99.88% temporal-filter, and 99.63% answerability accuracy over all 3,269 development records;
  - LoRA `rank16_l16`: 95.63% full-intent, 97.89% temporal-filter, and 97.71% answerability accuracy over all 3,269 development records.
- Updated `draft/main.tex` with expanded cross-family prompt-only rows, adapter rank/layer ablation table, and discussion of adapter placement.
- Added `scripts/run_remaining_planner_ablations.sh`.
- Started remaining planner ablation plan:
  1. `answerable_only` SFT to test whether unsupported examples are necessary;
  2. `no_prompt_mask` SFT to test whether assistant-only loss masking matters;
  3. `english_only` SFT to test bilingual transfer to Vietnamese dev prompts.
- These are dev-only ablations and must not change the frozen final-test method.
- Completed remaining planner ablations on dev64:
  - `answerable_only`: 100.00% JSON, 87.50% core/full, 87.50% answerability, 87.50% temporal-filter;
  - `no_prompt_mask`: 100.00% JSON, 79.69% core, 76.56% full, 87.50% answerability, 90.63% temporal-filter;
  - `english_only`: 100.00% JSON, 76.56% core, 73.44% full, 93.75% answerability, 85.94% temporal-filter.
- Updated `draft/main.tex` with an additional planner objective/data controls table and discussion.
- Added `scripts/build_optional_audit_splits.py`.
- Added `scripts/run_optional_external_multilingual_audits.sh`.
- Completed optional external/multilingual audit plan:
  1. pull and run `mistral:7b` prompt-only dev64 smoke;
  2. build Vietnamese diacritic dev audit split from existing Vietnamese dev labels;
  3. build local non-World-Bank dev audit split from OWID/derived-source records;
  4. evaluate the frozen metadata-aware planner on both audit splits.
- Optional audit results:
  - `mistral:7b` prompt-only dev64: 100.00% JSON validity, 0.00% core/full intent accuracy;
  - `mixtral:8x7b` prompt-only dev64: 100.00% JSON validity, 0.00% core/full intent accuracy;
  - Vietnamese diacritic planner audit: n=1,332, 100.00% JSON, 81.68% core, 72.60% full, 81.83% answerability, 99.47% temporal-filter accuracy;
  - non-World-Bank planner audit: n=56, 100.00% JSON, 82.14% core, 76.79% full, 85.71% answerability, 94.64% temporal-filter accuracy.
- Updated `draft/main.tex`, `experiment_plan.md`, `training/ablation_protocol.md`, and `notes/doctoral_core_execution_plan.md` with the optional audit evidence.
- Added `scripts/build_dissertation_rigor_package.py`.
- Generated dissertation-rigor package under `runs/dissertation_rigor_20260621/`:
  - 28 bootstrap confidence-interval rows;
  - 20 paired McNemar-style tests;
  - 37 final-test slice rows;
  - 30 optional-audit slice rows;
  - 19 final-test task-confusion rows;
  - reproducibility file check with no missing required artifacts.
- Added `REPRODUCIBILITY.md`.
- Generated figures under `figures/`:
  - `ft_tip_architecture.pdf`;
  - `final_test_ci.pdf`;
  - `final_failure_decomposition.pdf`.
- Updated `draft/main.tex` with architecture, statistical reliability, paired-test, CI, and failure-decomposition figures/tables.
- Recompiled `draft/main.pdf` and copied the 26-page PDF to `Paper09_FT_TIP_working_manuscript.pdf`.
- Pulled local `mixtral:8x7b` via Ollama and ran full dev64 prompt-only smoke under `runs/mixtral_prompt_smoke_20260621/`.
- Updated `draft/main.tex`, `experiment_plan.md`, `training/ablation_protocol.md`, and `notes/doctoral_core_execution_plan.md` with the Mixtral prompt-only negative-control row.

## Overnight Full-Dev Run

- Started a detached `screen` runner at 2026-06-19 23:11 +07: `paper09_overnight`.
- Enabled a separate `screen` sleep-prevention session until 2026-06-20 06:00 +07: `paper09_caffeinate`.
- Runner script: `scripts/run_overnight_full_dev_until_6am.sh`.
- Run directory: `runs/overnight_full_dev_20260619/`.
- Live log: `runs/overnight_full_dev_20260619/overnight.log`.
- The runner resumes partial JSONL outputs and evaluates, in order:
  1. metadata-aware Qwen2.5 LoRA on full expanded dev;
  2. unsupported-x4 metadata-aware Qwen2.5 LoRA on full expanded dev;
  3. schema-only Qwen2.5 LoRA on full expanded dev;
  4. prompt-only Qwen2.5 full expanded dev if time remains.
- At that overnight-dev stage, the expanded test split remained untouched; it was later evaluated once after the protocol freeze.

## Paper Identity

This paper should be method-first:

```text
mathematical formulation -> model/fine-tuning objective -> algorithm -> experiment
```

The empirical section should prove the model argument, not replace it.
