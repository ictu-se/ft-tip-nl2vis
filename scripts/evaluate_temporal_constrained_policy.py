#!/usr/bin/env python3
"""Evaluate a conservative temporal-constrained planner+gate policy.

The learned planner and learned gate still decide the intent. This script only
applies a deterministic temporal-support constraint when an otherwise answerable
prediction emits a malformed or unsupported temporal_filter. The constraint is
deliberately narrow and is reported separately as a policy action.
"""

from __future__ import annotations

import argparse
import json
import re
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


def canonical_temporal_filter(task_type: str, metadata: dict[str, Any]) -> str | None:
    try:
        ymin = int(metadata["year_min"])
        ymax = int(metadata["year_max"])
        recent_start = int(metadata["recent_10_start"])
        recent_end = int(metadata["recent_10_end"])
        previous_start = int(metadata["previous_10_start"])
        previous_end = int(metadata["previous_10_end"])
        latest = int(metadata["latest_year"])
    except (KeyError, TypeError, ValueError):
        return None

    if task_type in {"temporal_boundary_check", "temporal_trend"}:
        return f"{ymin}-{ymax}" if task_type == "temporal_boundary_check" else "all_years"
    if task_type == "temporal_recent_window":
        return f"last_10_years:{recent_start}-{recent_end}"
    if task_type == "temporal_previous_window":
        return f"previous_10_years:{previous_start}-{previous_end}"
    if task_type == "mixed_temporal_distribution":
        return f"year:{latest}"
    if task_type == "mixed_temporal_ranking":
        return "latest_year"
    return None


def valid_temporal_filter(value: Any, metadata: dict[str, Any]) -> bool:
    text = str(value or "").strip()
    if text in {"", "monthly"}:
        return text == "monthly"
    if text in {"all_years", "latest_year"}:
        return True
    try:
        ymin = int(metadata["year_min"])
        ymax = int(metadata["year_max"])
    except (KeyError, TypeError, ValueError):
        return False

    def valid_year(year: int) -> bool:
        return ymin <= year <= ymax

    match = re.fullmatch(r"(\d{4})-(\d{4})", text)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        return start <= end and valid_year(start) and valid_year(end)
    match = re.fullmatch(r"(last_10_years|previous_10_years):(\d{4})-(\d{4})", text)
    if match:
        start, end = int(match.group(2)), int(match.group(3))
        return start <= end and valid_year(start) and valid_year(end)
    match = re.fullmatch(r"year:(\d{4})", text)
    if match:
        return valid_year(int(match.group(1)))
    match = re.fullmatch(r"before_after:(\d{4})", text)
    if match:
        return valid_year(int(match.group(1)))
    return False


def apply_temporal_constraint(
    prediction: dict[str, Any] | None,
    metadata: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, str, str]:
    if not isinstance(prediction, dict):
        return prediction, "no_prediction", "", ""
    if prediction.get("answerability") != "answerable":
        return prediction, "not_answerable", str(prediction.get("temporal_filter") or ""), ""
    before = str(prediction.get("temporal_filter") or "").strip()
    if valid_temporal_filter(before, metadata):
        return prediction, "unchanged_valid", before, before
    task = str(prediction.get("task_type") or "").strip()
    candidate = canonical_temporal_filter(task, metadata)
    if not candidate:
        return prediction, "unchanged_no_candidate", before, ""
    repaired = dict(prediction)
    repaired["temporal_filter"] = candidate
    return repaired, "temporal_constraint_repair", before, candidate


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
    actions = sorted({row["temporal_constraint_action"] for row in rows})
    out["temporal_constraint_action"] = {
        action: sum(row["temporal_constraint_action"] == action for row in rows) for action in actions
    }
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
    parser.add_argument("--composed", type=Path, required=True)
    parser.add_argument("--dev-records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    metadata_by_id = {
        str(row["sample_id"]): row.get("temporal_metadata", {}) for row in read_jsonl(args.dev_records)
    }
    rows = []
    for row in read_jsonl(args.composed):
        sample_id = str(row["sample_id"])
        pred, action, before, after = apply_temporal_constraint(
            row.get("prediction"), metadata_by_id.get(sample_id, {})
        )
        scores = score_prediction(pred, row["gold"])
        out = dict(row)
        out.update(
            {
                "prediction": pred,
                "pre_constraint_prediction": row.get("prediction"),
                "temporal_constraint_action": action,
                "temporal_filter_before_constraint": before,
                "temporal_filter_after_constraint": after,
                **scores,
            }
        )
        rows.append(out)

    write_jsonl(args.output, rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summarize(rows), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
