# Value-preserving display repair: saved-output evidence

This version supports the retention analysis of 86 adaptively reused VisEval queries, two model families and nine configurations. It contains 1,548 scored outputs, all ten before/after repair captures, actual chart examples, source rows for all eight figures, and portable analysis code. The full historical repository remains available alongside this version.

## Reproduce the saved-output analysis

Use Python 3.11 or later:

```bash
cd retention_20261029
python3 scripts/reproduce_counts.py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/reproduce_intervals.py
.venv/bin/python scripts/make_tables.py
.venv/bin/python scripts/empirical_figures.py
```

The count audit requires only the Python standard library. The other commands reproduce 36 complete-output intervals, three numerical tables, and eight figures. The figure script uses archived native PNGs and repair SVGs without changing their chart contents. `all_ten_repairs.html` displays every intervention. `MANIFEST.json` hashes the files in this version. No image-generation model is used.

## Scope and limitations

This is saved-output reconciliation, **not fresh-inference replication**. No new model calls are made. It does not provide all original campaign environments, full raw inference logs or model blobs. The full fresh-inference package remains incomplete; do not infer independent validation or a compute-matched comparison from these files. Code and results for older experiments at the repository root concern different panels.

The data show that replacement can improve complete-output counts while causing numerical losses. The permutation preserves selected values, including incorrect ones. Native-system comparisons favor the complete pipeline on this adaptive slice, while incremental intervals against shared-pool structural fallback include or touch zero.

## Provenance

The scores and before/after captures are unchanged from the retained experiments. Only file organization and the plotting script's input paths were refactored for portability. The two reproduced chart pairs are original experimental artifacts. VisEval reference objects and their MIT license are attributed in `THIRD_PARTY_NOTICES.txt`. This package includes no manuscript source, manuscript PDF, editorial correspondence, secrets or model weights.

## Additional executable evidence (2026-10-30)

`repair_replay/` now executes the frozen display rule on all 172 saved choices
and renders the ten eligible charts. A clean-directory run reproduced every
decision, specification, physical capture and SVG byte for byte. See its README
for the Node/Vega setup and command. This is deterministic repair replay, not
fresh upstream model inference.

`supporting_panels/` restores earlier prepared-annual and mark-retention evidence
already described in the manuscript. Run `python scripts/reproduce_supporting_panels.py`
to reconcile the 2,200 saved prepared-panel scores and 128 original mark-panel
records. These overlapping development panels are never pooled with the public
86-query slice. Full historical training and model-inference replay remain out
of scope for this portable release.
