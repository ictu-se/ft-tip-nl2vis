#!/usr/bin/env python3
"""Run a schema-rich few-shot Ollama baseline for Paper 09."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_composed_policy import score_prediction  # noqa: E402


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
            if limit is not None and len(records) >= limit:
                break
    return records


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            continue
    return None


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
        out[f"{key}_pct"] = 100 * sum(bool(row.get(key)) for row in rows) / n if n else 0.0
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
    return out


def ollama_chat(model: str, messages: list[dict[str, str]], *, timeout: int) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "num_ctx": 8192},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        obj = json.loads(response.read().decode("utf-8"))
    return str(obj.get("message", {}).get("content", ""))


FEWSHOT_TASKS = [
    "temporal_recent_window",
    "temporal_previous_window",
    "temporal_granularity_unanswerable",
    "stat_unanswerable",
    "mixed_change_ranking",
]


def schema_block(record: dict[str, Any]) -> str:
    lines = []
    for item in record.get("schema") or []:
        lines.append(
            "name={name} | type={type} | role={role} | unit={unit}".format(
                name=item.get("name", ""),
                type=item.get("type", ""),
                role=item.get("role", ""),
                unit=item.get("unit", ""),
            )
        )
    return "\n".join(lines)


def metadata_block(record: dict[str, Any]) -> str:
    meta = record.get("temporal_metadata") or {}
    keys = [
        "time_field",
        "year_min",
        "year_max",
        "distinct_years",
        "recent_10_start",
        "recent_10_end",
        "previous_10_start",
        "previous_10_end",
        "temporal_granularity",
        "latest_year",
    ]
    return "\n".join(f"{key}={meta.get(key, '')}" for key in keys)


def compact_record(record: dict[str, Any], include_gold: bool) -> str:
    body = (
        f"Dataset title: {record.get('dataset_title', '')}\n"
        f"Domain: {record.get('domain', '')}\n"
        f"Source: {record.get('source', '')}\n"
        f"Language: {record.get('language', '')}\n"
        f"Query: {record.get('query', '')}\n\n"
        f"Schema fields:\n{schema_block(record)}\n\n"
        f"Temporal support metadata:\n{metadata_block(record)}\n"
    )
    if include_gold:
        body += "\nGold JSON:\n" + json.dumps(record["gold_intent"], ensure_ascii=False, sort_keys=True)
    return body


def build_fewshots(train_records: list[dict[str, Any]], shots: int) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_records:
        by_task[str(row.get("task_type", ""))].append(row)
    selected = []
    for task in FEWSHOT_TASKS:
        if by_task.get(task):
            selected.append(by_task[task][0])
        if len(selected) >= shots:
            return selected
    for row in train_records:
        if row not in selected:
            selected.append(row)
        if len(selected) >= shots:
            break
    return selected


def build_messages(record: dict[str, Any], exemplars: list[dict[str, Any]]) -> list[dict[str, str]]:
    schema_keys = [
        "aggregation",
        "answerability",
        "chart_type",
        "group_by",
        "measure",
        "required_fields",
        "secondary_measure",
        "sort",
        "statistic",
        "task_type",
        "temporal_filter",
        "temporal_granularity",
        "time_field",
        "top_k",
        "unsupported_reason",
    ]
    system = (
        "You are a schema-rich NL2Vis temporal intent planner. Output one valid JSON object only. "
        "Use exactly these keys: "
        + ", ".join(schema_keys)
        + ". Never invent dataset fields. Use temporal metadata to compute recent, previous, latest, and boundary windows. "
        "If the query asks for monthly data over annual year data, future forecasting, or city fields not in the schema, output an unanswerable intent."
    )
    user_parts = ["Few-shot examples:"]
    for i, ex in enumerate(exemplars, start=1):
        user_parts.append(f"\nExample {i}\n{compact_record(ex, include_gold=True)}")
    user_parts.append("\nNow infer the JSON intent for this record:\n" + compact_record(record, include_gold=False))
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n".join(user_parts)}]


def stratified(records: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    if limit is None or limit >= len(records):
        return records
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        groups[(str(row.get("task_type", "")), str(row.get("language", "")))].append(row)
    for group in groups.values():
        group.sort(key=lambda row: str(row.get("sample_id", "")))
    selected = []
    keys = sorted(groups)
    while keys and len(selected) < limit:
        next_keys = []
        for key in keys:
            group = groups[key]
            if group and len(selected) < limit:
                selected.append(group.pop(0))
            if group:
                next_keys.append(key)
        keys = next_keys
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--shots", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--progress-every", type=int, default=5)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    train_records = read_jsonl(args.train)
    records = stratified(read_jsonl(args.input), args.limit)
    exemplars = build_fewshots(train_records, args.shots)

    rows: list[dict[str, Any]] = []
    done_ids = set()
    if args.resume and args.output.exists():
        rows = read_jsonl(args.output)
        done_ids = {str(row.get("sample_id")) for row in rows}
    elif args.output.exists():
        args.output.unlink()

    started = time.time()
    for index, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id"))
        if sample_id in done_ids:
            continue
        messages = build_messages(record, exemplars)
        raw_output = ollama_chat(args.model, messages, timeout=args.timeout)
        pred = extract_json_object(raw_output)
        gold = record["gold_intent"]
        scores = score_prediction(pred, gold)
        row = {
            "index": index,
            "sample_id": record.get("sample_id"),
            "dataset_id": record.get("dataset_id"),
            "language": record.get("language"),
            "task_type": record.get("task_type"),
            "raw_output": raw_output,
            "prediction": pred,
            "gold": gold,
            **scores,
        }
        rows.append(row)
        append_jsonl(args.output, row)
        if args.progress_every > 0 and len(rows) % args.progress_every == 0:
            elapsed = time.time() - started
            print(f"processed {len(rows)}/{len(records)} in {elapsed:.1f}s", file=sys.stderr, flush=True)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize(rows)
    summary.update(
        {
            "model": args.model,
            "shots": args.shots,
            "limit": args.limit,
            "exemplar_sample_ids": [row.get("sample_id") for row in exemplars],
        }
    )
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
