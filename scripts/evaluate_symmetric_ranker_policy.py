#!/usr/bin/env python3
"""Evaluate a symmetric-order ranker decision policy.

For each positive/negative pair, the policy compares the original-order ranker
prediction with the swapped-order prediction. A decision is accepted only when
both orders select the same underlying candidate. Otherwise the pair is marked
order-sensitive and should fall back to a planner/constrained policy or require
additional verification.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
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


def normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text.startswith("A"):
        return "A"
    if text.startswith("B"):
        return "B"
    return text


def flip_label(label: str) -> str:
    if label == "A":
        return "B"
    if label == "B":
        return "A"
    return ""


def base_pair_id(pair_id: str) -> str:
    return pair_id.removesuffix("_swapped")


def evaluate(original_rows: list[dict[str, Any]], swapped_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    swapped_by_base = {base_pair_id(str(row["pair_id"])): row for row in swapped_rows}
    pair_rows = []
    for original in original_rows:
        pair_id = str(original["pair_id"])
        swapped = swapped_by_base.get(pair_id)
        if not swapped:
            continue
        original_pred = normalize_label(original.get("pred_label"))
        swapped_pred = normalize_label(swapped.get("pred_label"))
        selected_in_original_space_from_swapped = flip_label(swapped_pred)
        consistent = bool(original_pred and original_pred == selected_in_original_space_from_swapped)
        gold = normalize_label(original.get("gold_label"))
        symmetric_ok = consistent and original_pred == gold
        pair_rows.append(
            {
                "pair_id": pair_id,
                "sample_id": original.get("sample_id"),
                "dataset_id": original.get("dataset_id"),
                "language": original.get("language"),
                "task_type": original.get("task_type"),
                "hard_negative_type": original.get("hard_negative_type"),
                "gold_label": gold,
                "original_pred_label": original_pred,
                "swapped_pred_label": swapped_pred,
                "selected_label_original_space": original_pred if consistent else "",
                "symmetric_consistent": consistent,
                "symmetric_pairwise_ok": symmetric_ok,
                "original_pairwise_ok": bool(original.get("pairwise_ok")),
                "swapped_pairwise_ok": bool(swapped.get("pairwise_ok")),
            }
        )

    sample_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        sample_groups[str(row["sample_id"])].append(row)

    sample_rows = []
    for sample_id, rows in sorted(sample_groups.items()):
        consistent_n = sum(bool(row["symmetric_consistent"]) for row in rows)
        correct_n = sum(bool(row["symmetric_pairwise_ok"]) for row in rows)
        sample_rows.append(
            {
                "sample_id": sample_id,
                "dataset_id": rows[0].get("dataset_id"),
                "language": rows[0].get("language"),
                "task_type": rows[0].get("task_type"),
                "ranker_pairs": len(rows),
                "symmetric_consistent_pairs": consistent_n,
                "symmetric_correct_pairs": correct_n,
                "all_pairs_consistent": consistent_n == len(rows),
                "all_pairs_correct": correct_n == len(rows),
                "majority_pairs_correct": correct_n > len(rows) / 2,
                "any_order_sensitive_pair": consistent_n < len(rows),
            }
        )

    task_summary = {}
    for task in sorted({str(row.get("task_type")) for row in pair_rows}):
        group = [row for row in pair_rows if str(row.get("task_type")) == task]
        task_summary[task] = {
            "n": len(group),
            "consistent_pct": pct(sum(row["symmetric_consistent"] for row in group), len(group)),
            "symmetric_pairwise_ok_pct": pct(sum(row["symmetric_pairwise_ok"] for row in group), len(group)),
        }

    summary = {
        "pair_n": len(pair_rows),
        "sample_n": len(sample_rows),
        "pair_symmetric_consistent_pct": pct(sum(row["symmetric_consistent"] for row in pair_rows), len(pair_rows)),
        "pair_symmetric_ok_pct": pct(sum(row["symmetric_pairwise_ok"] for row in pair_rows), len(pair_rows)),
        "pair_order_sensitive_pct": pct(sum(not row["symmetric_consistent"] for row in pair_rows), len(pair_rows)),
        "sample_all_pairs_consistent_pct": pct(sum(row["all_pairs_consistent"] for row in sample_rows), len(sample_rows)),
        "sample_all_pairs_correct_pct": pct(sum(row["all_pairs_correct"] for row in sample_rows), len(sample_rows)),
        "sample_majority_pairs_correct_pct": pct(sum(row["majority_pairs_correct"] for row in sample_rows), len(sample_rows)),
        "sample_any_order_sensitive_pair_pct": pct(sum(row["any_order_sensitive_pair"] for row in sample_rows), len(sample_rows)),
        "order_sensitive_by_task_type": dict(
            sorted(Counter(row["task_type"] for row in pair_rows if not row["symmetric_consistent"]).items())
        ),
        "by_task_type": task_summary,
    }
    return summary, pair_rows, sample_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--swapped", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    summary, pair_rows, sample_rows = evaluate(read_jsonl(args.original), read_jsonl(args.swapped))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "symmetric_ranker_policy_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_jsonl(args.out_dir / "symmetric_ranker_policy_pairs.jsonl", pair_rows)
    write_jsonl(args.out_dir / "symmetric_ranker_policy_samples.jsonl", sample_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
