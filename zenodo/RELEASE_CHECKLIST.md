# Zenodo Release Checklist

Before making the release public:

1. Replace `TO_BE_CONFIRMED` in `CITATION.cff`, `.zenodo.json`, and `LICENSE`.
2. Confirm the public GitHub repository URL.
3. Decide whether adapter checkpoints should be public. If yes, attach them as GitHub release assets or upload them directly to Zenodo.
4. Create a GitHub release, e.g. `v1.0.0`.
5. Archive the release through Zenodo.
6. Copy the Zenodo DOI into the manuscript Data and Code Availability section.

Suggested manuscript wording:

```text
The code, benchmark splits, and experimental artifacts supporting this study
are archived at Zenodo: DOI TO_BE_FILLED_AFTER_RELEASE. The repository excludes
the manuscript source and contains the frozen evaluation commands, expanded
benchmark splits, final-test outputs, statistical summaries, and chart-level
audit artifacts.
```
