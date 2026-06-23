#!/usr/bin/env python3
"""Generate manuscript table for schema-rich few-shot prompt baselines."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "fewshot_schema_baseline_20260621"


ROWS = [
    ("Mistral-7B, 5-shot schema-rich", RUN_DIR / "mistral7b_dev48_summary.json"),
    ("Qwen2.5-Coder-14B, 5-shot schema-rich", RUN_DIR / "qwen25coder14b_dev48_summary.json"),
]


def fmt(value: float) -> str:
    return f"{value:.2f}"


def main() -> None:
    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Prompt baseline & n & JSON & Full & Answer. & Temp. filter & False plot \\",
        r"\midrule",
    ]
    for label, path in ROWS:
        item = json.loads(path.read_text(encoding="utf-8"))
        lines.append(
            "{} & {} & {} & {} & {} & {} & {} \\\\".format(
                label,
                item["n"],
                fmt(item["json_ok_pct"]),
                fmt(item["full_intent_ok_pct"]),
                fmt(item["answerability_ok_pct"]),
                fmt(item["temporal_filter_ok_pct"]),
                fmt(item["false_plot_rate_pct"]),
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    (RUN_DIR / "fewshot_schema_baseline_table.tex").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
