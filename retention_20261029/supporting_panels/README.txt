EARLIER SUPPORTING PANELS — 2026-10-30

Run: python scripts/reproduce_supporting_panels.py

prepared_annual_case_scores.json: 2,200 saved case-level scores, representing
220 shared requests x five configurations x two families. Each configuration
has 199 reference-executed requests and 21 nonexecution references, across 15
source datasets. These are NOT 2,200 independent requests. Prepared annual
relations remove source recovery and are not the final raw-table pipeline.

mark_retention_cases.json: 64 original requests x two families, with 57 executed
references per family, original/combined plans' saved numerical relations and
component scores. The same requests under free/schema decoding are not
independent repeats. Gemma numerical retention is 53 -> 45 (1 gain, 9 losses);
Qwen is 34 -> 34 (1 gain, 1 loss). Both favorable mark results and numerical
regressions remain visible. The full campaign's summary retains its FAILED
joint allocation gate and eight exploratory interaction intervals.

These files support the earlier-panel claims already in the current manuscript.
They are saved-score and relation exports. The checker reconciles case counts;
it does not claim to repeat training, native model inference or original
reference construction. No results are added to the public 86-query denominator.
SOURCE_PROVENANCE.json traces each export to the unchanged local campaign.
