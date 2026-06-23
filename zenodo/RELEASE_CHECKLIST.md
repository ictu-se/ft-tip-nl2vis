# Zenodo Release Checklist

Before making the release public:

1. Confirm the public GitHub repository URL.
2. Decide whether adapter checkpoints should be public. If yes, attach them as GitHub release assets or upload them directly to Zenodo.
3. Create a GitHub release, e.g. `v1.0.1`.
4. Archive the release through Zenodo.
5. Copy the Zenodo DOI into the manuscript Data and Code Availability section.

Suggested manuscript wording:

```text
The code, benchmark splits, and experimental artifacts supporting this study
are archived at Zenodo: https://doi.org/10.5281/zenodo.20819042. The repository excludes
the manuscript source and contains the frozen evaluation commands, expanded
benchmark splits, final-test outputs, statistical summaries, and chart-level
audit artifacts.
```
