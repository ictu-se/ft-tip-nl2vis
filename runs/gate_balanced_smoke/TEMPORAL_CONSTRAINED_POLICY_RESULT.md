# Temporal-Constrained Planner+Gate Policy Result

Date: 2026-06-20

This evaluation adds a conservative temporal-support constraint on top of the
learned metadata planner and learned answerability gate. The constraint is
applied only when an answerable prediction emits a malformed or unsupported
`temporal_filter`. It uses the temporal support metadata already provided to the
model in the prompt.

## Full Expanded-Dev Result

| Metric | Planner+Gate | Planner+Gate+Temporal Constraint |
| --- | ---: | ---: |
| Development records | 3,269 | 3,269 |
| JSON validity | 100.00% | 100.00% |
| Answerability accuracy | 99.17% | 99.17% |
| Temporal-filter accuracy | 93.09% | 93.15% |
| Core-intent accuracy | 88.10% | 88.16% |
| Full-intent accuracy | 87.95% | 88.01% |
| False-plot rate | 0.83% | 0.83% |
| Over-refusal rate | 0.00% | 0.00% |
| Temporal constraint repairs | - | 2 |

## Temporal Candidate Subset

On the 1,573 development samples for which hard-negative temporal candidates
exist, the temporal-constrained policy reaches:

| Metric | Value |
| --- | ---: |
| Core accuracy | 98.92% |
| Full accuracy | 98.79% |
| Temporal-filter accuracy | 100.00% |
| Temporal-filter failures | 0 |

## Interpretation

The constraint repairs exactly two malformed Vietnamese temporal-boundary
outputs (`1-12-2003-2019` and `1-12`) into the metadata-supported range
`2003-2019`. It does not change answerability behavior, false plotting, or
over-refusal. This supports the final policy design:

```text
learned planner -> learned answerability gate -> temporal support constraint -> learned ranker/verifier
```

The temporal constraint should be described as a decoding/validation layer, not
as the main learned contribution. The learned contribution remains the
planner--gate--ranker decomposition.

## Artifacts

- Outputs:
  `runs/gate_balanced_smoke/composed_metadata_planner_gate_temporal_constrained_outputs.jsonl`
- Summary:
  `runs/gate_balanced_smoke/composed_metadata_planner_gate_temporal_constrained_summary.json`
- Temporal subset/ranker integration analysis:
  `runs/ranker_hard_negative_smoke/policy_integration_analysis_temporal_constrained/ranker_policy_integration_summary.json`
