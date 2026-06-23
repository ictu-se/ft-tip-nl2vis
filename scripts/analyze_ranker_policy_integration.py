#!/usr/bin/env python3
"""Analyze how the hard-negative ranker can support a planner+gate policy.

This script does not claim that the final planner--gate--ranker policy is already
implemented. It measures the sample-level evidence needed before that step:
whether the trained ranker consistently selects the gold intent over all
constructed temporal hard negatives, and whether observed planner temporal
errors match negatives that the ranker already rejects.
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


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def temporal_filter(intent: dict[str, Any] | None) -> str:
    if not isinstance(intent, dict):
        return ""
    return normalize_value(intent.get("temporal_filter"))


def task_type(intent: dict[str, Any] | None) -> str:
    if not isinstance(intent, dict):
        return ""
    return normalize_value(intent.get("task_type"))


def analyze(
    composed_rows: list[dict[str, Any]],
    ranker_pairs: list[dict[str, Any]],
    ranker_outputs: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    pairs_by_id = {str(row["pair_id"]): row for row in ranker_pairs}
    outputs_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ranker_outputs:
        pair = pairs_by_id.get(str(row.get("pair_id")))
        if pair:
            merged = dict(row)
            merged["positive_intent"] = pair.get("positive_intent")
            merged["negative_intent"] = pair.get("negative_intent")
            outputs_by_sample[str(row["sample_id"])].append(merged)

    composed_by_sample = {str(row["sample_id"]): row for row in composed_rows}
    sample_rows = []
    repair_rows = []

    for sample_id, rows in sorted(outputs_by_sample.items()):
        composed = composed_by_sample.get(sample_id)
        n = len(rows)
        correct = sum(bool(row.get("pairwise_ok")) for row in rows)
        gold = composed.get("gold") if composed else rows[0].get("positive_intent")
        pred = composed.get("prediction") if composed else None
        planner_pred = composed.get("planner_prediction") if composed else None
        negative_filters = {temporal_filter(row.get("negative_intent")) for row in rows}
        pred_filter = temporal_filter(pred)
        planner_filter = temporal_filter(planner_pred)
        gold_filter = temporal_filter(gold)
        pred_matches_negative = bool(pred_filter and pred_filter in negative_filters)
        planner_matches_negative = bool(planner_filter and planner_filter in negative_filters)
        matching_negative_rows = [
            row for row in rows if temporal_filter(row.get("negative_intent")) in {pred_filter, planner_filter}
        ]
        rejected_matching_negative = any(bool(row.get("pairwise_ok")) for row in matching_negative_rows)

        sample_row = {
            "sample_id": sample_id,
            "dataset_id": composed.get("dataset_id") if composed else rows[0].get("dataset_id"),
            "language": composed.get("language") if composed else rows[0].get("language"),
            "task_type": composed.get("task_type") if composed else task_type(gold),
            "ranker_pairs": n,
            "ranker_correct_pairs": correct,
            "ranker_all_correct": correct == n,
            "ranker_majority_correct": correct > n / 2,
            "ranker_any_error": correct < n,
            "policy_core_ok": bool(composed.get("core_intent_ok")) if composed else None,
            "policy_full_ok": bool(composed.get("full_intent_ok")) if composed else None,
            "policy_temporal_filter_ok": bool(composed.get("temporal_filter_ok")) if composed else None,
            "gold_temporal_filter": gold_filter,
            "policy_temporal_filter": pred_filter,
            "planner_temporal_filter": planner_filter,
            "policy_filter_matches_constructed_negative": pred_matches_negative,
            "planner_filter_matches_constructed_negative": planner_matches_negative,
            "ranker_rejects_matching_negative": rejected_matching_negative,
        }
        sample_rows.append(sample_row)

        if composed and not bool(composed.get("temporal_filter_ok")):
            repair_rows.append(sample_row)

    ranker_sample_n = len(sample_rows)
    ranker_pair_n = len(ranker_outputs)
    temporal_policy_rows = [
        row for row in composed_rows if str(row.get("sample_id")) in outputs_by_sample
    ]
    temporal_policy_failures = [
        row for row in temporal_policy_rows if not bool(row.get("temporal_filter_ok"))
    ]
    repairable_failures = [
        row for row in repair_rows
        if row["policy_filter_matches_constructed_negative"] and row["ranker_rejects_matching_negative"]
    ]
    planner_repairable_failures = [
        row for row in repair_rows
        if row["planner_filter_matches_constructed_negative"] and row["ranker_rejects_matching_negative"]
    ]

    summary = {
        "ranker_pair_n": ranker_pair_n,
        "ranker_pairwise_accuracy_pct": pct(sum(bool(row.get("pairwise_ok")) for row in ranker_outputs), ranker_pair_n),
        "ranker_sample_n": ranker_sample_n,
        "ranker_sample_all_correct_pct": pct(sum(row["ranker_all_correct"] for row in sample_rows), ranker_sample_n),
        "ranker_sample_majority_correct_pct": pct(sum(row["ranker_majority_correct"] for row in sample_rows), ranker_sample_n),
        "ranker_sample_any_error_pct": pct(sum(row["ranker_any_error"] for row in sample_rows), ranker_sample_n),
        "temporal_policy_sample_n": len(temporal_policy_rows),
        "temporal_policy_core_ok_pct": pct(sum(bool(row.get("core_intent_ok")) for row in temporal_policy_rows), len(temporal_policy_rows)),
        "temporal_policy_full_ok_pct": pct(sum(bool(row.get("full_intent_ok")) for row in temporal_policy_rows), len(temporal_policy_rows)),
        "temporal_policy_temporal_filter_ok_pct": pct(
            sum(bool(row.get("temporal_filter_ok")) for row in temporal_policy_rows),
            len(temporal_policy_rows),
        ),
        "temporal_policy_temporal_filter_failures": len(temporal_policy_failures),
        "failures_matching_constructed_negative": len(
            [row for row in repair_rows if row["policy_filter_matches_constructed_negative"]]
        ),
        "failures_repairable_by_existing_ranker_pair": len(repairable_failures),
        "planner_failures_repairable_by_existing_ranker_pair": len(planner_repairable_failures),
        "ranker_errors_by_task_type": dict(
            sorted(Counter(row["task_type"] for row in sample_rows if row["ranker_any_error"]).items())
        ),
    }
    return summary, sample_rows, repair_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--composed", type=Path, required=True)
    parser.add_argument("--ranker-pairs", type=Path, required=True)
    parser.add_argument("--ranker-outputs", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    summary, sample_rows, repair_rows = analyze(
        read_jsonl(args.composed),
        read_jsonl(args.ranker_pairs),
        read_jsonl(args.ranker_outputs),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "ranker_policy_integration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_jsonl(args.out_dir / "ranker_sample_verification.jsonl", sample_rows)
    write_jsonl(args.out_dir / "temporal_filter_failure_repair_analysis.jsonl", repair_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
