# Ranker Policy Integration Analysis

Date: 2026-06-20

This analysis joins the full-dev planner+gate composed policy with the full-dev
hard-negative ranker outputs. It does not claim that the final
planner--gate--ranker policy is implemented. Instead, it measures whether the
ranker is strong enough at the sample level to support such a policy.

## Inputs

- Composed planner+gate outputs:
  `runs/gate_balanced_smoke/composed_metadata_planner_gate_outputs.jsonl`
- Ranker raw development pairs:
  `training/gate_ranker_artifacts/ranker_dev_pairs.jsonl`
- Full-dev ranker outputs:
  `runs/ranker_hard_negative_smoke/full_dev_ranker_outputs.jsonl`

## Results

| Metric | Value |
| --- | ---: |
| Ranker pairwise dev pairs | 9,338 |
| Ranker pairwise accuracy | 98.49% |
| Ranker sample count | 1,573 |
| Samples where ranker rejects all constructed negatives | 92.37% |
| Samples where ranker majority prefers gold | 99.68% |
| Samples with any ranker pair error | 7.63% |
| Planner+gate temporal-policy samples | 1,573 |
| Planner+gate core accuracy on temporal-policy samples | 98.79% |
| Planner+gate full accuracy on temporal-policy samples | 98.66% |
| Planner+gate temporal-filter accuracy on temporal-policy samples | 99.87% |
| Planner+gate temporal-filter failures | 2 |
| Failures repairable by existing constructed negatives | 0 |

## Interpretation

The ranker is strong as a verifier: at the pair level it reaches 98.49% and at
the sample level it selects the gold intent by majority for 99.68% of temporal
candidate sets. The composed planner+gate policy is already very strong on the
same temporal subset, with only two temporal-filter failures.

The two remaining failures are not repaired by existing hard-negative pairs
because the planner outputs malformed temporal ranges (`1-12-2003-2019` and
`1-12`) rather than one of the constructed plausible temporal negatives. This
means the next model step should add candidate generation or constrained
temporal-range normalization before ranker selection, rather than only adding
more of the same hard-negative pairs.

## Artifacts

- Summary:
  `runs/ranker_hard_negative_smoke/policy_integration_analysis/ranker_policy_integration_summary.json`
- Sample-level verification:
  `runs/ranker_hard_negative_smoke/policy_integration_analysis/ranker_sample_verification.jsonl`
- Remaining temporal-filter failures:
  `runs/ranker_hard_negative_smoke/policy_integration_analysis/temporal_filter_failure_repair_analysis.jsonl`
