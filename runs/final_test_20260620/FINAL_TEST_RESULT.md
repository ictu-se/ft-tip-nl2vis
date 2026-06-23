# Paper 09 Final Expanded-Test Result

Date completed: 2026-06-20 23:42 +07

This is the frozen one-time expanded-test evaluation specified in
`FINAL_TEST_COMMANDS.md`. The method was not changed after observing these
results.

## Intent Policy Results

| Variant | n | JSON | Core | Full | Answer. | Temporal filter | False plot | Over-refuse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Metadata planner | 3,111 | 100.00 | 84.02 | 83.83 | 85.21 | 93.67 | - | - |
| Gate | 3,111 | 100.00 | - | - | 99.10 | - | 0.90 | 0.00 |
| Planner + gate + temporal constraint | 3,111 | 100.00 | 88.49 | 88.30 | 99.10 | 93.73 | 0.90 | 0.00 |

The temporal-support constraint repaired 2 malformed test predictions and did
not change answerability behavior.

## Ranker Results

| Metric | Original | Swapped |
| --- | ---: | ---: |
| Pairs | 8,850 | 8,850 |
| JSON validity | 100.00 | 100.00 |
| Pairwise accuracy | 98.34 | 98.25 |
| Accuracy when gold is A | 96.70 | 96.47 |
| Accuracy when gold is B | 100.00 | 100.00 |

## Position-Bias And Symmetric Policy

| Metric | Value |
| --- | ---: |
| Both orders correct | 96.59 |
| Original-only correct | 1.75 |
| Swapped-only correct | 1.66 |
| Both wrong | 0.00 |
| Order-sensitive pairs | 3.41 |
| Symmetric pair-level consistent/correct | 96.59 |
| Symmetric sample majority-correct | 98.06 |
| Symmetric sample all-pairs-correct | 85.75 |
| Samples with any fallback pair | 14.25 |

Order sensitivity is concentrated in `mixed_change_ranking` at 19.86%.
Direct temporal window tasks remain highly stable: `temporal_boundary_check`
and `temporal_period_filter` both have 0.00% order sensitivity.

## Interpretation

The test result supports the development-set conclusion. The learned gate
substantially improves answerability safety over the planner alone, the
temporal-support constraint handles rare malformed temporal strings, and the
ranker remains strong under original and swapped candidate orders. The residual
weakness is not basic temporal-window discrimination; it is order sensitivity
and semantic subtlety in mixed change-ranking tasks.

## Artifacts

- `planner_test_summary.json`
- `gate_test_summary.json`
- `composed_planner_gate_temporal_constrained_test_summary.json`
- `ranker_test_summary.json`
- `ranker_test_swapped_summary.json`
- `ranker_position_bias/ranker_position_bias_summary.json`
- `symmetric_ranker_policy/symmetric_ranker_policy_summary.json`
