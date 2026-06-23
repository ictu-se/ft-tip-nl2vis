# Ranker Position-Bias Analysis Result

Date: 2026-06-20

This analysis evaluates the trained hard-negative ranker on the original
development ranking pairs and on a swapped-order version where Candidate A and
Candidate B are reversed for every pair.

## Full-Dev Original vs Swapped

| Metric | Original | Swapped |
| --- | ---: | ---: |
| Pairs | 9,338 | 9,338 |
| JSON validity | 100.00% | 100.00% |
| Pairwise accuracy | 98.49% | 98.48% |
| Accuracy when gold is A | 96.95% | 96.99% |
| Accuracy when gold is B | 100.00% | 100.00% |

## Paired Analysis

| Pair class | Count / Rate |
| --- | ---: |
| Both original and swapped correct | 9,055 / 96.97% |
| Original only correct | 142 / 1.52% |
| Swapped only correct | 141 / 1.51% |
| Both wrong | 0 / 0.00% |
| Order-sensitive pairs | 283 / 3.03% |

## Order Sensitivity By Task Type

| Task type | n | Order-sensitive |
| --- | ---: | ---: |
| mixed_change_ranking | 726 | 18.46% |
| temporal_recent_window | 1,452 | 5.10% |
| stat_change | 1,452 | 3.31% |
| temporal_previous_window | 1,452 | 1.65% |
| temporal_boundary_check | 1,448 | 0.21% |
| temporal_period_filter | 1,404 | 0.00% |
| stat_average_period | 1,404 | 0.00% |

## Interpretation

The full swapped-order run shows that the ranker is not globally dependent on
candidate order: original and swapped accuracies are nearly identical. However,
3.03% of pairs are order-sensitive, concentrated mostly in
`mixed_change_ranking`. The final manuscript should therefore report the ranker
as strong but not perfectly position-invariant.

For the final policy, a symmetric evaluation strategy is recommended: when the
ranker is used to decide between two candidates, score both candidate orders or
use a tie/consistency rule for order-sensitive cases.

## Artifacts

- Swapped outputs:
  `runs/ranker_hard_negative_smoke/swapped_full_dev_ranker_outputs.jsonl`
- Swapped summary:
  `runs/ranker_hard_negative_smoke/swapped_full_dev_ranker_summary.json`
- Paired summary:
  `runs/ranker_hard_negative_smoke/position_bias_analysis/ranker_position_bias_summary.json`
- Paired records:
  `runs/ranker_hard_negative_smoke/position_bias_analysis/ranker_position_bias_pairs.jsonl`
