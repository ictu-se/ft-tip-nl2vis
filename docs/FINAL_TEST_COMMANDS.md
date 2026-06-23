# Paper 09 Final Test Commands

Frozen: 2026-06-20

This file records the exact final expanded-test command sequence before the
test split is evaluated. The selected method is:

```text
metadata-aware planner
  -> learned answerability gate
  -> temporal-support constraint
  -> symmetric-order hard-negative ranker/verifier with fallback
```

The final runner is:

```bash
cd "/Users/nguyenthevinh/Library/CloudStorage/GoogleDrive-vinhnt@tnu.edu.vn/My Drive/NL2Vis_GenAI_Research_2025_2026/manuscripts/09_finetuned_temporal_intent_planner_nl2vis"
bash scripts/run_final_test_once.sh
```

The detached execution command is:

```bash
screen -dmS paper09_final_test bash -lc "cd '/Users/nguyenthevinh/Library/CloudStorage/GoogleDrive-vinhnt@tnu.edu.vn/My Drive/NL2Vis_GenAI_Research_2025_2026/manuscripts/09_finetuned_temporal_intent_planner_nl2vis' && bash scripts/run_final_test_once.sh > runs/final_test_20260620/final_test.log 2>&1"
screen -dmS paper09_final_test_caffeinate caffeinate -dimsu -t 28800
```

## Frozen Inputs

- Planner test input:
  `benchmark_expanded/paper09_expanded_test_with_temporal_metadata_sft.jsonl`
- Test records with temporal metadata:
  `benchmark_expanded/paper09_expanded_test.jsonl`
- Test ranking pairs:
  `benchmark_expanded/paper09_expanded_test_ranking_pairs.jsonl`

## Frozen Model Components

- Base model:
  `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- Planner adapter:
  `training/adapters/qwen25_15b_expanded_metadata_smoke`
- Gate adapter:
  `training/adapters/qwen25_15b_gate_balanced_smoke`
- Ranker adapter:
  `training/adapters/qwen25_15b_ranker_hard_negative_smoke`

## Frozen Output Directory

All final test outputs are written under:

```text
runs/final_test_20260620/
```

Expected outputs:

- `planner_test_outputs.jsonl`
- `planner_test_summary.json`
- `gate_test_outputs.jsonl`
- `gate_test_summary.json`
- `composed_planner_gate_test_outputs.jsonl`
- `composed_planner_gate_test_summary.json`
- `composed_planner_gate_temporal_constrained_test_outputs.jsonl`
- `composed_planner_gate_temporal_constrained_test_summary.json`
- `ranker_test_outputs.jsonl`
- `ranker_test_summary.json`
- `ranker_test_swapped_outputs.jsonl`
- `ranker_test_swapped_summary.json`
- `ranker_position_bias/ranker_position_bias_summary.json`
- `symmetric_ranker_policy/symmetric_ranker_policy_summary.json`

## Rule

After this command sequence is run, do not change the method based on test
results. Only report the test results and analyze failures.
