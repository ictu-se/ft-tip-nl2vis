#!/usr/bin/env python3
"""Summarize schema/minmax/full-metadata leakage ablation outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_interval(value: Any) -> tuple[int, int] | None:
    text = str(value or "").strip()
    patterns = [
        r"^(?:last_10_years|previous_10_years):(?P<s>\d{4})-(?P<e>\d{4})$",
        r"^(?P<s>\d{4})-(?P<e>\d{4})$",
        r"^(?P<s>\d{4})_to_(?P<e>\d{4})$",
        r"^year:(?P<s>\d{4})$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            start = int(match.group("s"))
            end = int(match.groupdict().get("e") or start)
            return start, end
    return None


def summarize(label: str, path: Path) -> dict[str, Any]:
    rows = read_jsonl(path)
    n = len(rows)
    if n == 0:
        raise ValueError(f"No rows in {path}")
    bounded_errors: list[int] = []
    bounded_exact = 0
    false_plot = 0
    for row in rows:
        gold = row.get("gold") or {}
        pred = row.get("prediction") or {}
        if gold.get("answerability") == "unanswerable" and pred.get("answerability") == "answerable":
            false_plot += 1
        gold_interval = parse_interval(gold.get("temporal_filter"))
        pred_interval = parse_interval(pred.get("temporal_filter"))
        if gold_interval is not None and pred_interval is not None:
            err = abs(pred_interval[0] - gold_interval[0]) + abs(pred_interval[1] - gold_interval[1])
            bounded_errors.append(err)
            if err == 0:
                bounded_exact += 1
    return {
        "label": label,
        "n": n,
        "json_ok_pct": pct(rows, "json_ok"),
        "full_intent_ok_pct": pct(rows, "full_intent_ok"),
        "temporal_filter_ok_pct": pct(rows, "temporal_filter_ok"),
        "core_intent_ok_pct": pct(rows, "core_intent_ok"),
        "answerability_ok_pct": pct(rows, "answerability_ok"),
        "false_plot_all_pct": 100 * false_plot / n,
        "false_plot_count": false_plot,
        "bounded_n": len(bounded_errors),
        "boundary_exact_pct": 100 * bounded_exact / len(bounded_errors) if bounded_errors else None,
        "mean_boundary_error": sum(bounded_errors) / len(bounded_errors) if bounded_errors else None,
        "path": str(path),
    }


def pct(rows: list[dict[str, Any]], key: str) -> float:
    return 100 * sum(bool(row.get(key)) for row in rows) / len(rows)


def write_latex(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Input metadata & Full & Temp. filter & Boundary error & Boundary exact & False plot\\\\",
        "\\midrule",
    ]
    for row in rows:
        mean_err = row["mean_boundary_error"]
        boundary_exact = row["boundary_exact_pct"]
        lines.append(
            f"{row['label']} & "
            f"{row['full_intent_ok_pct']:.2f} & "
            f"{row['temporal_filter_ok_pct']:.2f} & "
            f"{mean_err:.2f} & "
            f"{boundary_exact:.2f} & "
            f"{row['false_plot_all_pct']:.2f}\\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--minmax", type=Path, required=True)
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--tex", type=Path, required=True)
    args = parser.parse_args()

    rows = [
        summarize("Schema-only", args.schema),
        summarize("Schema + min/max", args.minmax),
        summarize("Full metadata", args.full),
    ]
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_latex(rows, args.tex)
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
