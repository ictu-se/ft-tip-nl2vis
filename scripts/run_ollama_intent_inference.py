#!/usr/bin/env python3
"""Run Ollama prompt-only intent planner inference and structured evaluation."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from run_mlx_intent_inference import (  # noqa: E402
    append_jsonl,
    extract_json_object,
    read_jsonl,
    score_prediction,
    summarize,
)


def ollama_chat(model: str, messages: list[dict[str, str]], *, timeout: int) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    records = read_jsonl(args.input, args.limit)
    rows: list[dict[str, Any]] = []
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
        raw_output = ollama_chat(args.model, messages, timeout=args.timeout)
        pred = extract_json_object(raw_output)
        gold = json.loads(record["messages"][2]["content"])
        scores = score_prediction(pred, gold)
        row = {
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
