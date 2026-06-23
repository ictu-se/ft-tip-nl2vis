#!/usr/bin/env python3
"""Evaluate a planner + answerability-gate composed policy on expanded dev."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CORE_KEYS = [
    "answerability",
    "task_type",
    "time_field",
    "measure",
    "temporal_filter",
    "statistic",
]

FULL_KEYS = [
    "answerability",
    "task_type",
    "time_field",
    "measure",
    "secondary_measure",
    "group_by",
    "chart_type",
    "temporal_filter",
    "temporal_granularity",
    "statistic",
    "aggregation",
    "sort",
    "top_k",
    "unsupported_reason",
]


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


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return sorted(str(item).strip() for item in value)
    return value


def field_f1(predicted: Any, gold: Any) -> float:
    pred_set = set(normalize_value(predicted or []))
    gold_set = set(normalize_value(gold or []))
    if not pred_set and not gold_set:
        return 1.0
    if not pred_set or not gold_set:
        return 0.0
    tp = len(pred_set & gold_set)
    precision = tp / len(pred_set)
    recall = tp / len(gold_set)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_prediction(pred: dict[str, Any] | None, gold: dict[str, Any]) -> dict[str, Any]:
    if pred is None:
        return {
            "json_ok": False,
            "core_intent_ok": False,
            "full_intent_ok": False,
            "required_field_f1": 0.0,
            **{f"{key}_ok": False for key in CORE_KEYS},
        }
    scores = {"json_ok": True}
    for key in CORE_KEYS:
        scores[f"{key}_ok"] = normalize_value(pred.get(key)) == normalize_value(gold.get(key))
    scores["core_intent_ok"] = all(scores[f"{key}_ok"] for key in CORE_KEYS)
    scores["full_intent_ok"] = all(
        normalize_value(pred.get(key)) == normalize_value(gold.get(key)) for key in FULL_KEYS
    ) and normalize_value(pred.get("required_fields")) == normalize_value(gold.get("required_fields"))
    scores["required_field_f1"] = field_f1(pred.get("required_fields"), gold.get("required_fields"))
    return scores


def normalize_answerability(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"answerable", "supported", "true", "yes", "1"}:
        return "answerable"
    if text in {"unanswerable", "unsupported", "false", "no", "0"}:
        return "unanswerable"
    return text


def make_refusal_intent(gold: dict[str, Any], planner_pred: dict[str, Any] | None, gate_pred: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(gold)
    if planner_pred:
        for key in ["task_type", "temporal_filter", "temporal_granularity", "statistic"]:
            if planner_pred.get(key):
                base[key] = planner_pred.get(key)
    reason = ""
    if gate_pred:
        reason = str(gate_pred.get("unsupported_reason") or "").strip()
    if not reason:
        reason = str(gold.get("unsupported_reason") or "").strip()
    base.update(
        {
            "answerability": "unanswerable",
            "required_fields": [],
            "time_field": "",
            "measure": "",
            "secondary_measure": "",
            "group_by": "",
            "chart_type": "none",
            "aggregation": "none",
            "sort": "none",
            "top_k": None,
            "unsupported_reason": reason,
        }
    )
    return base


def compose_prediction(planner_row: dict[str, Any], gate_row: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    planner_pred = planner_row.get("prediction")
    gate_pred = gate_row.get("prediction")
    gate_answerability = normalize_answerability(gate_row.get("pred_answerability"))
    gold = planner_row["gold"]
    if gate_answerability == "unanswerable":
        return make_refusal_intent(gold, planner_pred, gate_pred), "gate_refusal"
    if gate_answerability == "answerable":
        return planner_pred, "planner_allowed"
    return planner_pred, "gate_unknown_planner_allowed"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    bool_keys = [
        "json_ok",
        "answerability_ok",
        "task_type_ok",
        "time_field_ok",
        "measure_ok",
        "temporal_filter_ok",
        "statistic_ok",
        "core_intent_ok",
        "full_intent_ok",
    ]
    out = {"n": n}
    for key in bool_keys:
        out[f"{key}_pct"] = 100 * sum(bool(row[key]) for row in rows) / n if n else 0.0
    out["required_field_f1"] = sum(float(row.get("required_field_f1") or 0.0) for row in rows) / n if n else 0.0
    out["false_plot_rate_pct"] = 100 * sum(
        row["gold"]["answerability"] == "unanswerable"
        and row["prediction"]
        and row["prediction"].get("answerability") == "answerable"
        for row in rows
    ) / n if n else 0.0
    out["over_refusal_rate_pct"] = 100 * sum(
        row["gold"]["answerability"] == "answerable"
        and row["prediction"]
        and row["prediction"].get("answerability") == "unanswerable"
        for row in rows
    ) / n if n else 0.0
    out["policy_action"] = dict(
        sorted(
            {
                action: sum(row["policy_action"] == action for row in rows)
                for action in {row["policy_action"] for row in rows}
            }.items()
        )
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--planner", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    planner_rows = read_jsonl(args.planner)
    gate_by_id = {str(row["sample_id"]): row for row in read_jsonl(args.gate)}
    out_rows = []
    for planner_row in planner_rows:
        sample_id = str(planner_row["sample_id"])
        gate_row = gate_by_id[sample_id]
        pred, action = compose_prediction(planner_row, gate_row)
        scores = score_prediction(pred, planner_row["gold"])
        out_rows.append(
            {
                "sample_id": sample_id,
                "dataset_id": planner_row.get("dataset_id"),
                "language": planner_row.get("language"),
                "task_type": planner_row.get("task_type"),
                "policy_action": action,
                "gate_prediction": gate_row.get("prediction"),
                "planner_prediction": planner_row.get("prediction"),
                "prediction": pred,
                "gold": planner_row["gold"],
                **scores,
            }
        )

    write_jsonl(args.output, out_rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summarize(out_rows), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
