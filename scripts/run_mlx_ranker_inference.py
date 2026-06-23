#!/usr/bin/env python3
"""Run MLX/MLX-LM pairwise ranker inference and evaluation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


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


def normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text.startswith("A"):
        return "A"
    if text.startswith("B"):
        return "B"
    return text


def gold_label(record: dict[str, Any]) -> str:
    gold = json.loads(record["messages"][2]["content"])
    return normalize_label(gold.get("positive_label") or gold.get("preferred"))


def pred_label(pred: dict[str, Any] | None) -> str:
    if pred is None:
        return ""
    return normalize_label(pred.get("positive_label") or pred.get("preferred"))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    labels = sorted({row["gold_label"] for row in rows})
    out: dict[str, Any] = {
        "n": n,
        "json_ok_pct": 100 * sum(bool(row["json_ok"]) for row in rows) / n,
        "pairwise_accuracy_pct": 100 * sum(bool(row["pairwise_ok"]) for row in rows) / n,
    }
    for label in labels:
        group = [row for row in rows if row["gold_label"] == label]
        out[f"gold_{label}_n"] = len(group)
        out[f"gold_{label}_accuracy_pct"] = 100 * sum(bool(row["pairwise_ok"]) for row in group) / len(group)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter-path")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-tokens", type=int, default=96)
    parser.add_argument("--temp", type=float, default=0.0)
    parser.add_argument("--progress-every", type=int, default=50)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    model, tokenizer = load(args.model, adapter_path=args.adapter_path)
    sampler = make_sampler(args.temp)
    records = read_jsonl(args.input, args.limit)
    rows = []
    done_ids = set()
    if args.resume and args.output.exists():
        rows = read_jsonl(args.output)
        done_ids = {str(row.get("pair_id")) for row in rows}
    elif args.output.exists():
        args.output.unlink()

    for index, record in enumerate(records, start=1):
        pair_id = str(record.get("pair_id"))
        if pair_id in done_ids:
            continue
        messages = record["messages"][:2]
        prompt_tokens = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_dict=False)
        raw_output = generate(
            model,
            tokenizer,
            prompt_tokens,
            max_tokens=args.max_tokens,
            sampler=sampler,
            verbose=False,
        )
        pred = extract_json_object(raw_output)
        gold = gold_label(record)
        pred_choice = pred_label(pred)
        row = {
            "index": index,
            "pair_id": pair_id,
            "sample_id": record.get("sample_id"),
            "dataset_id": record.get("dataset_id"),
            "language": record.get("language"),
            "task_type": record.get("task_type"),
            "hard_negative_type": record.get("hard_negative_type"),
            "json_ok": pred is not None,
            "gold_label": gold,
            "pred_label": pred_choice,
            "pairwise_ok": pred_choice == gold,
            "prediction": pred,
            "raw_output": raw_output,
        }
        rows.append(row)
        append_jsonl(args.output, row)
        if args.progress_every > 0 and len(rows) % args.progress_every == 0:
            print(f"processed {len(rows)}/{len(records)}", file=sys.stderr, flush=True)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summarize(rows), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
