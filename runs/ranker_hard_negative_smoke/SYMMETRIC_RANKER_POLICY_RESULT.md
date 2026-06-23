# Symmetric-Order Ranker Policy Result

Date: 2026-06-20

This result converts the original-vs-swapped ranker analysis into a
consistency-aware decision policy. For each pair, the ranker is evaluated in
both candidate orders. A decision is accepted only when both orders select the
same underlying candidate.

## Pair-Level Result

| Metric | Value |
| --- | ---: |
| Pairs | 9,338 |
| Symmetric consistent decisions | 96.97% |
| Symmetric pairwise-correct decisions | 96.97% |
| Order-sensitive decisions requiring fallback | 3.03% |

No consistently wrong pair appears in this dev analysis: inconsistent cases are
the order-sensitive pairs already identified by the original-vs-swapped study.

## Sample-Level Result

| Metric | Value |
| --- | ---: |
| Temporal-candidate samples | 1,573 |
| All pair decisions consistent/correct | 87.54% |
| Majority pair decisions correct | 98.54% |
| Any order-sensitive pair | 12.46% |

The strict all-pairs criterion is lower because each sample has multiple hard
negative pairs. A single order-sensitive negative is enough to mark the whole
sample as not fully consistent. The majority criterion is more relevant for a
candidate-selection policy, but the final paper should report both.

## Task-Level Sensitivity

| Task type | Pairs | Symmetric correct / consistent |
| --- | ---: | ---: |
| stat_average_period | 1,404 | 100.00% |
| temporal_period_filter | 1,404 | 100.00% |
| temporal_boundary_check | 1,448 | 99.79% |
| temporal_previous_window | 1,452 | 98.35% |
| stat_change | 1,452 | 96.69% |
| temporal_recent_window | 1,452 | 94.90% |
| mixed_change_ranking | 726 | 81.54% |

## Interpretation

The ranker remains scientifically useful, but the final policy should not use a
single candidate order as if it were position-invariant. The recommended
decision rule is:

```text
Run ranker in both candidate orders.
If both orders select the same underlying candidate, accept the decision.
If the orders disagree, fall back to the constrained planner/gate policy or send
the case to a stronger verifier.
```

This is an honest final-policy rule: it improves reliability without hiding the
remaining order sensitivity in mixed change-ranking cases.

## Artifacts

- Summary:
  `runs/ranker_hard_negative_smoke/symmetric_ranker_policy/symmetric_ranker_policy_summary.json`
- Pair-level records:
  `runs/ranker_hard_negative_smoke/symmetric_ranker_policy/symmetric_ranker_policy_pairs.jsonl`
- Sample-level records:
  `runs/ranker_hard_negative_smoke/symmetric_ranker_policy/symmetric_ranker_policy_samples.jsonl`
