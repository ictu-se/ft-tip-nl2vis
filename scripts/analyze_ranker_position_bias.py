#!/usr/bin/env python3
"""Analyze original-vs-swapped ranker outputs for candidate-position bias."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def pct(num: int | float, den: int | float) -> float:
    return 100.0 * num / den if den else 0.0


def base_pair_id(pair_id: str) -> str:
    return pair_id.removesuffix("_swapped")


def summarize_bool(rows: list[dict[str, Any]], key: str) -> float:
    return pct(sum(bool(row.get(key)) for row in rows), len(rows))


def analyze(original_rows: list[dict[str, Any]], swapped_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    original_by_id = {str(row["pair_id"]): row for row in original_rows}
    paired = []
    missing_original = 0
    for swapped in swapped_rows:
        original = original_by_id.get(base_pair_id(str(swapped["pair_id"])))
        if not original:
            missing_original += 1
            continue
        pair_class = (
            "both_correct"
            if original.get("pairwise_ok") and swapped.get("pairwise_ok")
            else "original_only"
            if original.get("pairwise_ok") and not swapped.get("pairwise_ok")
            else "swapped_only"
            if not original.get("pairwise_ok") and swapped.get("pairwise_ok")
            else "both_wrong"
        )
        paired.append(
            {
                "pair_id": original["pair_id"],
                "sample_id": original.get("sample_id"),
                "dataset_id": original.get("dataset_id"),
                "language": original.get("language"),
                "task_type": original.get("task_type"),
                "hard_negative_type": original.get("hard_negative_type"),
                "original_gold_label": original.get("gold_label"),
                "original_pred_label": original.get("pred_label"),
                "original_ok": bool(original.get("pairwise_ok")),
                "swapped_gold_label": swapped.get("gold_label"),
                "swapped_pred_label": swapped.get("pred_label"),
                "swapped_ok": bool(swapped.get("pairwise_ok")),
                "pair_class": pair_class,
            }
        )

    class_counts = Counter(row["pair_class"] for row in paired)
    by_task = {}
    for task in sorted({str(row.get("task_type")) for row in paired}):
        group = [row for row in paired if str(row.get("task_type")) == task]
        by_task[task] = {
            "n": len(group),
            "both_correct_pct": pct(sum(row["pair_class"] == "both_correct" for row in group), len(group)),
            "order_sensitive_pct": pct(
                sum(row["pair_class"] in {"original_only", "swapped_only"} for row in group),
                len(group),
            ),
        }

    summary: dict[str, Any] = {
        "original_n": len(original_rows),
        "swapped_n": len(swapped_rows),
        "paired_n": len(paired),
        "missing_original_n": missing_original,
        "original_accuracy_pct": summarize_bool(original_rows, "pairwise_ok"),
        "swapped_accuracy_pct": summarize_bool(swapped_rows, "pairwise_ok"),
        "paired_original_accuracy_pct": pct(sum(row["original_ok"] for row in paired), len(paired)),
        "paired_swapped_accuracy_pct": pct(sum(row["swapped_ok"] for row in paired), len(paired)),
        "both_correct_pct": pct(class_counts["both_correct"], len(paired)),
        "original_only_pct": pct(class_counts["original_only"], len(paired)),
        "swapped_only_pct": pct(class_counts["swapped_only"], len(paired)),
        "both_wrong_pct": pct(class_counts["both_wrong"], len(paired)),
        "order_sensitive_pct": pct(
            class_counts["original_only"] + class_counts["swapped_only"],
            len(paired),
        ),
        "pair_class_counts": dict(sorted(class_counts.items())),
        "by_task_type": by_task,
    }
    return summary, paired


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--swapped", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    summary, paired = analyze(read_jsonl(args.original), read_jsonl(args.swapped))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "ranker_position_bias_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_jsonl(args.out_dir / "ranker_position_bias_pairs.jsonl", paired)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
