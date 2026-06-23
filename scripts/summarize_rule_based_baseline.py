#!/usr/bin/env python3
"""Generate manuscript table for the Paper 09 rule-based baseline."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "rule_based_temporal_baseline_20260621"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: float) -> str:
    return f"{value:.2f}"


def main() -> None:
    dev = read(RUN_DIR / "dev_summary.json")
    test = read(RUN_DIR / "test_summary.json")
    rows = [
        ("Development", dev),
        ("Frozen test", test),
    ]
    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Split & Full & Answer. & Temp. filter & Statistic & False plot & Over-refuse \\",
        r"\midrule",
    ]
    for split, item in rows:
        lines.append(
            "{} & {} & {} & {} & {} & {} & {} \\\\".format(
                split,
                fmt(item["full_intent_ok_pct"]),
                fmt(item["answerability_ok_pct"]),
                fmt(item["temporal_filter_ok_pct"]),
                fmt(item["statistic_ok_pct"]),
                fmt(item["false_plot_rate_pct"]),
                fmt(item["over_refusal_rate_pct"]),
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    (RUN_DIR / "rule_based_baseline_table.tex").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
