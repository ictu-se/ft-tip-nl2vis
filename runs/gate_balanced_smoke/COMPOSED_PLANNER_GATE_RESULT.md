# Composed Metadata Planner + Gate Result

This evaluates the first composed FT-TIP policy on expanded dev:

```text
metadata-aware planner output + gate-balanced answerability decision
```

The expanded test split is untouched.

## Full Expanded-Dev Result

| Variant | Core intent | Full intent | Answerability | Temporal filter | False-plot | Over-refusal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Metadata planner only | 84.37% | 84.22% | 85.19% | 93.09% | 14.81% | 0.00% |
| Unsupported-x4 planner | 79.63% | 79.23% | 86.85% | 85.81% | 0.24% | 12.91% |
| Metadata planner + gate | 88.10% | 87.95% | 99.17% | 93.09% | 0.83% | 0.00% |

## Policy Actions

| Action | Count |
| --- | ---: |
| Planner allowed | 2,812 |
| Gate refusal | 457 |

## Interpretation

The separate answerability gate improves both safety and aggregate structured
intent accuracy. Unlike unsupported-x4 planner-only SFT, it does not solve false
plotting by refusing answerable requests. This supports the architecture claim
that answerability should be modeled as a dedicated gate rather than folded
only into the sequence planner objective.

The remaining main model component is the hard-negative ranker for temporal
window discrimination. The next row should test:

```text
metadata planner + gate + ranker
```

on expanded dev before any final test evaluation.
