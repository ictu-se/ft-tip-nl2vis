#!/usr/bin/env python3
"""Rule-based temporal baseline for Paper 09.

This is a non-learned control: it uses only query text, schema fields, and
runtime temporal metadata to form an intent. It should be read as a strong
metadata-aware heuristic baseline, not as the proposed method.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_composed_policy import score_prediction, summarize  # noqa: E402


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


def ascii_fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", ascii_fold(text))


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", ascii_fold(text)))


def schema_names(record: dict[str, Any], role: str | None = None) -> list[str]:
    names = []
    for item in record.get("schema") or []:
        if role and item.get("role") != role:
            continue
        names.append(str(item.get("name") or ""))
    return [name for name in names if name]


def time_field(record: dict[str, Any]) -> str:
    meta = record.get("temporal_metadata") or {}
    if meta.get("time_field"):
        return str(meta["time_field"])
    fields = schema_names(record, "time")
    return fields[0] if fields else "year"


def group_field(record: dict[str, Any]) -> str:
    for preferred in ["country", "country_name"]:
        if preferred in schema_names(record):
            return preferred
    dims = schema_names(record, "dimension")
    return dims[0] if dims else ""


def measure_fields(record: dict[str, Any]) -> list[str]:
    return schema_names(record, "measure")


def query_years(query: str) -> list[int]:
    return [int(year) for year in re.findall(r"\b(19\d{2}|20\d{2})\b", query)]


def match_measures(record: dict[str, Any], query: str) -> list[str]:
    q_fold = ascii_fold(query)
    q_compact = compact(query)
    q_words = words(query)
    scored = []
    for name in measure_fields(record):
        name_fold = ascii_fold(name.replace("_", " "))
        name_compact = compact(name)
        name_words = set(re.findall(r"[a-z0-9]+", name_fold))
        score = 0
        if name_compact and name_compact in q_compact:
            score += 100
        if name_fold and name_fold in q_fold:
            score += 80
        score += 5 * len(name_words & q_words)
        if score:
            scored.append((score, len(name), name))
    scored.sort(reverse=True)
    return [name for _, _, name in scored]


def required_fields(record: dict[str, Any], intent: dict[str, Any]) -> list[str]:
    fields = []
    for key in ["group_by", "measure", "secondary_measure", "time_field"]:
        value = intent.get(key)
        if value and value != "none" and value not in fields:
            fields.append(value)
    return sorted(fields)


def base_intent(record: dict[str, Any], measure: str) -> dict[str, Any]:
    return {
        "aggregation": "none",
        "answerability": "answerable",
        "chart_type": "line",
        "group_by": group_field(record),
        "measure": measure,
        "required_fields": [],
        "secondary_measure": "",
        "sort": "none",
        "statistic": "trend",
        "task_type": "temporal_trend",
        "temporal_filter": "all_years",
        "temporal_granularity": (record.get("temporal_metadata") or {}).get("temporal_granularity", "year"),
        "time_field": time_field(record),
        "top_k": None,
        "unsupported_reason": "",
    }


def refusal(record: dict[str, Any], task_type: str, statistic: str, temporal_filter: str, reason: str) -> dict[str, Any]:
    return {
        "aggregation": "none",
        "answerability": "unanswerable",
        "chart_type": "none",
        "group_by": "",
        "measure": "",
        "required_fields": [],
        "secondary_measure": "",
        "sort": "none",
        "statistic": statistic,
        "task_type": task_type,
        "temporal_filter": temporal_filter,
        "temporal_granularity": (record.get("temporal_metadata") or {}).get("temporal_granularity", "year"),
        "time_field": "",
        "top_k": None,
        "unsupported_reason": reason,
    }


def recent_range(meta: dict[str, Any]) -> tuple[int, int]:
    if meta.get("recent_10_start") and meta.get("recent_10_end"):
        return int(meta["recent_10_start"]), int(meta["recent_10_end"])
    end = int(meta.get("year_max") or meta.get("latest_year"))
    return end - 9, end


def previous_range(meta: dict[str, Any]) -> tuple[int, int]:
    if meta.get("previous_10_start") and meta.get("previous_10_end"):
        return int(meta["previous_10_start"]), int(meta["previous_10_end"])
    start, _ = recent_range(meta)
    return start - 10, start - 1


def infer_intent(record: dict[str, Any]) -> dict[str, Any]:
    query = str(record.get("query") or "")
    q = ascii_fold(query)
    meta = record.get("temporal_metadata") or {}
    matched = match_measures(record, query)
    measure = matched[0] if matched else (measure_fields(record)[0] if measure_fields(record) else "")
    intent = base_intent(record, measure)

    if "monthly" in q or "hang thang" in q:
        return refusal(
            record,
            "temporal_granularity_unanswerable",
            "trend",
            "monthly",
            "monthly granularity is not available; schema has annual year values",
        )
    if "forecast" in q or "forecasted" in q or "next year" in q or "du bao" in q or "nam sau" in q or "city" in q or "thanh pho" in q:
        return refusal(
            record,
            "stat_unanswerable",
            "forecast",
            "future",
            "forecast and city fields are not available",
        )

    years = query_years(query)
    group = group_field(record)
    latest = int(meta.get("latest_year") or meta.get("year_max") or (years[-1] if years else 0))
    y_min = int(meta.get("year_min") or latest)
    y_max = int(meta.get("year_max") or latest)
    recent_start, recent_end = recent_range(meta)
    prev_start, prev_end = previous_range(meta)

    if "relationship" in q or "correlation" in q or "moi quan he" in q:
        second = matched[1] if len(matched) > 1 else ""
        intent.update(
            {
                "chart_type": "scatter",
                "secondary_measure": second,
                "statistic": "correlation",
                "task_type": "stat_correlation_proxy",
                "temporal_filter": f"year:{years[-1] if years else latest}",
            }
        )
    elif ("rank" in q or "xep hang" in q) and ("growth" in q or "change" in q or "thay doi" in q):
        intent.update(
            {
                "chart_type": "bar",
                "statistic": "difference_top_k",
                "task_type": "mixed_change_ranking",
                "temporal_filter": f"{recent_start}_to_{recent_end}",
                "sort": "descending",
                "top_k": 5,
            }
        )
    elif "highest" in q or "top 5" in q or "rank the top" in q or "cao nhat" in q or "xep hang" in q:
        task = "mixed_temporal_ranking" if ("which countries" in q or "nuoc nao" in q) else "stat_ranking_topk"
        intent.update(
            {
                "chart_type": "bar",
                "statistic": "top_k",
                "task_type": task,
                "temporal_filter": "latest_year",
                "sort": "descending",
                "top_k": 5,
            }
        )
    elif "distribution" in q or "phan bo" in q:
        if years:
            task = "mixed_temporal_distribution"
            filt = f"year:{years[-1]}"
        else:
            task = "stat_distribution"
            filt = "all_years"
        intent.update({"chart_type": "boxplot", "statistic": "distribution", "task_type": task, "temporal_filter": filt})
    elif "outlier" in q or "unusually" in q or "bat thuong" in q:
        intent.update({"chart_type": "point", "statistic": "outlier", "task_type": "stat_outlier"})
    elif "before and after" in q or "truoc va sau" in q:
        pivot = years[-1] if years else (y_min + y_max) // 2
        intent.update(
            {
                "chart_type": "bar",
                "aggregation": "mean",
                "statistic": "mean",
                "task_type": "temporal_before_after",
                "temporal_filter": f"before_after:{pivot}",
            }
        )
    elif "average" in q or "trung binh" in q:
        start, end = (years[0], years[-1]) if len(years) >= 2 else (recent_start, recent_end)
        intent.update(
            {
                "chart_type": "bar",
                "aggregation": "mean",
                "statistic": "mean",
                "task_type": "stat_average_period",
                "temporal_filter": f"{start}-{end}",
            }
        )
    elif "change" in q or "growth" in q or "thay doi" in q:
        start, end = (years[0], years[-1]) if len(years) >= 2 else (recent_start, recent_end)
        intent.update(
            {
                "chart_type": "bar",
                "statistic": "difference",
                "task_type": "stat_change",
                "temporal_filter": f"{start}_to_{end}",
            }
        )
    elif (
        "exact data boundary" in q
        or "first available" in q
        or "ranh gioi" in q
        or "mien nam co trong du lieu" in q
        or "nam dau tien" in q
    ):
        intent.update(
            {
                "chart_type": "line",
                "statistic": "trend",
                "task_type": "temporal_boundary_check",
                "temporal_filter": f"{y_min}-{y_max}",
            }
        )
    elif "previous decade" in q or "decade before" in q or "thap ky truoc" in q or "thap ky lien truoc" in q:
        intent.update(
            {
                "chart_type": "line",
                "statistic": "trend",
                "task_type": "temporal_previous_window",
                "temporal_filter": f"previous_10_years:{prev_start}-{prev_end}",
            }
        )
    elif "most recent 10-year" in q or "recent 10-year" in q or "last decade" in q or "gan day" in q or "gan nhat" in q:
        intent.update(
            {
                "chart_type": "line",
                "statistic": "trend",
                "task_type": "temporal_recent_window",
                "temporal_filter": f"last_10_years:{recent_start}-{recent_end}",
            }
        )
    elif len(years) >= 2 and ("compare" in q or "from" in q or "so sanh" in q or "giai doan" in q):
        intent.update(
            {
                "chart_type": "bar",
                "statistic": "comparison",
                "task_type": "temporal_period_filter",
                "temporal_filter": f"{years[0]}-{years[-1]}",
            }
        )
    else:
        intent.update(
            {
                "chart_type": "line",
                "statistic": "trend",
                "task_type": "temporal_trend",
                "temporal_filter": "all_years",
            }
        )

    if not intent.get("group_by"):
        intent["group_by"] = group
    intent["required_fields"] = required_fields(record, intent)
    return intent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    out_rows = []
    for index, record in enumerate(read_jsonl(args.input), start=1):
        pred = infer_intent(record)
        gold = record["gold_intent"]
        scores = score_prediction(pred, gold)
        out_rows.append(
            {
                "index": index,
                "sample_id": record.get("sample_id"),
                "dataset_id": record.get("dataset_id"),
                "language": record.get("language"),
                "task_type": record.get("task_type"),
                "policy_action": "rule_based",
                "prediction": pred,
                "gold": gold,
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
