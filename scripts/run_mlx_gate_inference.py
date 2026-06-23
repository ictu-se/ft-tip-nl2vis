#!/usr/bin/env python3
"""Run MLX/MLX-LM answerability-gate inference and evaluation."""

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


def normalize_answerability(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"answerable", "supported", "true", "yes", "1"}:
        return "answerable"
    if text in {"unanswerable", "unsupported", "false", "no", "0"}:
        return "unanswerable"
    return text


def score(pred: dict[str, Any] | None, gold: dict[str, Any]) -> dict[str, Any]:
    gold_answerability = normalize_answerability(gold.get("answerability"))
    if pred is None:
        pred_answerability = ""
        json_ok = False
    else:
        json_ok = True
        if "answerability" in pred:
            pred_answerability = normalize_answerability(pred.get("answerability"))
        else:
            pred_answerability = normalize_answerability(pred.get("supported"))
    answerability_ok = pred_answerability == gold_answerability
    return {
        "json_ok": json_ok,
        "gold_answerability": gold_answerability,
        "pred_answerability": pred_answerability,
        "answerability_ok": answerability_ok,
        "false_plot": gold_answerability == "unanswerable" and pred_answerability == "answerable",
        "over_refusal": gold_answerability == "answerable" and pred_answerability == "unanswerable",
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    unanswerable = [r for r in rows if r["gold_answerability"] == "unanswerable"]
    answerable = [r for r in rows if r["gold_answerability"] == "answerable"]
    return {
        "n": n,
        "json_ok_pct": 100 * sum(r["json_ok"] for r in rows) / n,
        "answerability_ok_pct": 100 * sum(r["answerability_ok"] for r in rows) / n,
        "false_plot_rate_pct": 100 * sum(r["false_plot"] for r in rows) / n,
        "over_refusal_rate_pct": 100 * sum(r["over_refusal"] for r in rows) / n,
        "unanswerable_false_plot_pct": 100 * sum(r["false_plot"] for r in unanswerable) / len(unanswerable)
        if unanswerable
        else 0.0,
        "answerable_over_refusal_pct": 100 * sum(r["over_refusal"] for r in answerable) / len(answerable)
        if answerable
        else 0.0,
        "answerable_n": len(answerable),
        "unanswerable_n": len(unanswerable),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter-path")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-tokens", type=int, default=80)
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
        done_ids = {str(row.get("sample_id")) for row in rows}
    elif args.output.exists():
        args.output.unlink()

    for index, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id"))
        if sample_id in done_ids:
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
        gold = json.loads(record["messages"][2]["content"])
        scored = score(pred, gold)
        row = {
            "index": index,
            "sample_id": record.get("sample_id"),
            "dataset_id": record.get("dataset_id"),
            "language": record.get("language"),
            "task_type": record.get("task_type"),
            "raw_output": raw_output,
            "prediction": pred,
            "gold": gold,
            **scored,
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
