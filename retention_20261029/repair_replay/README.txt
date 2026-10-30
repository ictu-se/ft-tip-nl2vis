ACTUAL REPAIR REPLAY — 2026-10-30

From the retention_20261029 directory, install Python requirements and Node.js,
then run:
  npm --prefix repair_replay/vega_runtime ci --ignore-scripts --no-audit --no-fund
  python repair_replay/run.py --output /tmp/p09-repair-output
Choose a new output directory on every run. Node is resolved from PATH;
P09_NODE can select a specific Node executable. Vega is locked at 6.2.0 and
Vega-Lite compilation uses 5.16 through vl-convert-python 1.9.0.

inputs.json contains 172 saved choices and only fields consumed by the display
rule. It contains no gold correctness labels, original Python programs or model
rationales. The original display guard is copied unchanged. Repair functions,
coordinate normalization and Vega screen extraction are extracted from frozen
sources. The capture runtime changes only Node path resolution. Original source
hashes are recorded in SOURCE_PROVENANCE.json.

The runner fixes decisions and renders eligible outputs before reading expected.json.
It then verifies all 172 decisions, 10 specifications and 10 physical captures
against the archive. Every new rendering must preserve the exact canonical
pair multiset and bar mark and satisfy the predicted display contract.
SVG byte equality is reported separately; geometry/data equality is required.

A clean temporary-directory replay passed: 172/172 decisions and 10/10 SVGs
match. This executes the actual deterministic repair, not just plotting saved
scores. It does not regenerate upstream model outputs and is not an independent
accuracy test. A wrong selected numerical relation remains wrong after repair.
