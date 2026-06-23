#!/usr/bin/env python3
"""Run MLX/MLX-LM intent planner inference and structured evaluation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler


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


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
            if limit is not None and len(records) >= limit:
                break
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    candidates = [text]
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            continue
    return None


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
        normalize_value(pred.get(key)) == normalize_value(gold.get(key))
        for key in FULL_KEYS
    ) and normalize_value(pred.get("required_fields")) == normalize_value(
        gold.get("required_fields")
    )
    scores["required_field_f1"] = field_f1(
        pred.get("required_fields"), gold.get("required_fields")
    )
    return scores


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}
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
    summary = {"n": n}
    for key in bool_keys:
        summary[f"{key}_pct"] = 100 * sum(bool(row[key]) for row in rows) / n
    summary["required_field_f1"] = sum(row["required_field_f1"] for row in rows) / n
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter-path")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-tokens", type=int, default=260)
    parser.add_argument("--temp", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    model, tokenizer = load(args.model, adapter_path=args.adapter_path)
    sampler = make_sampler(args.temp)
    records = read_jsonl(args.input, args.limit)
    rows = []
    done_ids = set()
    if args.resume and args.output.exists():
        rows = read_jsonl(args.output)
        done_ids = {str(row.get("sample_id")) for row in rows}
    elif args.output.exists():
        args.output.unlink()

    for index, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id"))
        if sample_id in done_ids:
            continue
        messages = record["messages"][:2]
        prompt_tokens = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_dict=False,
        )
        raw_output = generate(
            model,
            tokenizer,
            prompt_tokens,
            max_tokens=args.max_tokens,
            sampler=sampler,
            verbose=False,
        )
        pred = extract_json_object(raw_output)
        gold = json.loads(record["messages"][2]["content"])
        scores = score_prediction(pred, gold)
        rows.append(
            {
                "index": index,
                "sample_id": record.get("sample_id"),
                "dataset_id": record.get("dataset_id"),
                "language": record.get("language"),
                "task_type": record.get("task_type"),
                "answerability": record.get("answerability"),
                "raw_output": raw_output,
                "prediction": pred,
                "gold": gold,
                **scores,
            }
        )
        append_jsonl(args.output, rows[-1])
        if args.progress_every > 0 and len(rows) % args.progress_every == 0:
            print(f"processed {len(rows)}/{len(records)}", file=sys.stderr, flush=True)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summarize(rows), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
