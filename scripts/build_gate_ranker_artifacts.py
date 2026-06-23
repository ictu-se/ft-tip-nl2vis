#!/usr/bin/env python3
"""Build answerability-gate and hard-negative-ranker artifacts for Paper 09.

This is deterministic data infrastructure. It does not create labels with a
model and it does not use the expanded test split.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


INTENT_KEYS = [
    "answerability",
    "task_type",
    "required_fields",
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
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    return {key: intent.get(key) for key in INTENT_KEYS}


def schema_to_text(schema: list[dict[str, Any]]) -> str:
    fields = []
    for field in schema:
        fields.append(
            " | ".join(
                [
                    f"name={field.get('name', '')}",
                    f"type={field.get('type', '')}",
                    f"role={field.get('role', '')}",
                    f"unit={field.get('unit', '')}",
                ]
            )
        )
    return "\n".join(fields)


def temporal_metadata_to_text(tm: dict[str, Any]) -> str:
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
    return "\n".join(f"{key}={tm.get(key, '')}" for key in keys)


def context_text(record: dict[str, Any]) -> str:
    return (
        f"Dataset title: {record.get('dataset_title', '')}\n"
        f"Domain: {record.get('domain', '')}\n"
        f"Source: {record.get('source', '')}\n"
        f"Language: {record.get('language', '')}\n"
        f"Query: {record.get('query', '')}\n\n"
        "Schema fields:\n"
        f"{schema_to_text(record.get('schema', []))}\n\n"
        "Temporal support metadata:\n"
        f"{temporal_metadata_to_text(record.get('temporal_metadata', {}))}"
    )


def gate_record(record: dict[str, Any]) -> dict[str, Any]:
    gold = normalize_intent(record["gold_intent"])
    answerability = gold.get("answerability")
    output = {
        "answerability": answerability,
        "supported": answerability == "answerable",
        "unsupported_reason": gold.get("unsupported_reason", ""),
    }
    return {
        "sample_id": record["sample_id"],
        "dataset_id": record["dataset_id"],
        "language": record["language"],
        "task_type": record["task_type"],
        "answerability": answerability,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the answerability gate for a temporal-statistical NL2Vis planner. "
                    "Given a query, schema, and temporal support metadata, output only JSON "
                    "with answerability, supported, and unsupported_reason. Refuse only when "
                    "the request cannot be supported by the fields, granularity, statistic, "
                    "or temporal support."
                ),
            },
            {"role": "user", "content": context_text(record)},
            {"role": "assistant", "content": json.dumps(output, ensure_ascii=False, sort_keys=True)},
        ],
    }


def balanced_gate_records(records: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    answerable = [r for r in records if r["gold_intent"]["answerability"] == "answerable"]
    unanswerable = [r for r in records if r["gold_intent"]["answerability"] == "unanswerable"]
    rng = random.Random(seed)
    if not unanswerable:
        return [gate_record(r) for r in records]
    sampled_answerable = rng.sample(answerable, min(len(answerable), len(unanswerable)))
    balanced = sampled_answerable + unanswerable
    rng.shuffle(balanced)
    return [gate_record(r) for r in balanced]


def pair_context(pair: dict[str, Any], candidate_a: dict[str, Any], candidate_b: dict[str, Any]) -> str:
    record_like = {
        "dataset_title": "",
        "domain": "",
        "source": "",
        "language": pair.get("language", ""),
        "query": pair.get("query", ""),
        "schema": pair.get("schema", []),
        "temporal_metadata": pair.get("temporal_metadata", {}),
    }
    return (
        f"{context_text(record_like)}\n\n"
        "Candidate A:\n"
        f"{json.dumps(normalize_intent(candidate_a), ensure_ascii=False, sort_keys=True)}\n\n"
        "Candidate B:\n"
        f"{json.dumps(normalize_intent(candidate_b), ensure_ascii=False, sort_keys=True)}\n\n"
        "Choose the candidate that is better grounded in the query, schema, and temporal support."
    )


def ranker_record(pair: dict[str, Any], seed: int) -> dict[str, Any]:
    rng = random.Random(f"{seed}:{pair['pair_id']}")
    positive = normalize_intent(pair["positive_intent"])
    negative = normalize_intent(pair["negative_intent"])
    positive_first = rng.random() < 0.5
    candidate_a = positive if positive_first else negative
    candidate_b = negative if positive_first else positive
    preferred = "A" if positive_first else "B"
    output = {
        "preferred": preferred,
        "positive_label": preferred,
        "hard_negative_type": pair.get("hard_negative_type", ""),
        "reason": "preferred candidate matches the requested temporal/statistical commitment",
    }
    return {
        "pair_id": pair["pair_id"],
        "sample_id": pair["sample_id"],
        "dataset_id": pair["dataset_id"],
        "language": pair["language"],
        "task_type": pair["task_type"],
        "hard_negative_type": pair.get("hard_negative_type", ""),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an intent ranker/verifier for temporal-statistical NL2Vis. "
                    "Given two candidate intents, choose the one that is correctly grounded. "
                    "Output only JSON with preferred, positive_label, hard_negative_type, and reason."
                ),
            },
            {"role": "user", "content": pair_context(pair, candidate_a, candidate_b)},
            {"role": "assistant", "content": json.dumps(output, ensure_ascii=False, sort_keys=True)},
        ],
    }


def candidate_serialization_record(pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_id": pair["pair_id"],
        "sample_id": pair["sample_id"],
        "dataset_id": pair["dataset_id"],
        "language": pair["language"],
        "task_type": pair["task_type"],
        "query": pair["query"],
        "schema": pair["schema"],
        "temporal_metadata": pair["temporal_metadata"],
        "positive_intent": normalize_intent(pair["positive_intent"]),
        "negative_intent": normalize_intent(pair["negative_intent"]),
        "hard_negative_type": pair.get("hard_negative_type", ""),
    }


def summarize_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n": len(records),
        "answerability": dict(Counter(r["answerability"] for r in records)),
        "language": dict(Counter(r["language"] for r in records)),
        "task_type": dict(Counter(r["task_type"] for r in records)),
    }


def summarize_ranker(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n": len(records),
        "language": dict(Counter(r["language"] for r in records)),
        "task_type": dict(Counter(r["task_type"] for r in records)),
        "hard_negative_type": dict(Counter(r["hard_negative_type"] for r in records)),
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Paper 09 Gate And Ranker Artifacts",
        "",
        "These files are deterministic training/evaluation artifacts for the next FT-TIP model step.",
        "They use only expanded train/dev splits; the expanded test split is untouched.",
        "",
        "## Files",
        "",
        "- `gate_train.jsonl`, `gate_dev.jsonl`: answerability-gate SFT records.",
        "- `gate_train_balanced.jsonl`: balanced answerable/unanswerable gate training subset.",
        "- `ranker_train.jsonl`, `ranker_dev.jsonl`: pairwise hard-negative ranker SFT records.",
        "- `ranker_train_pairs.jsonl`, `ranker_dev_pairs.jsonl`: raw positive/negative intent pairs for custom margin losses.",
        "- `gate_ranker_summary.json`: split counts.",
        "",
        "## Intended Use",
        "",
        "- Train or prompt-evaluate the gate to reduce false plotting without creating over-refusal.",
        "- Train or prompt-evaluate the ranker to choose gold temporal windows over plausible hard negatives.",
        "- Combine planner candidates with gate/ranker decisions before any final test evaluation.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260620)
    args = parser.parse_args()

    splits = {}
    pairs = {}
    for split in ["train", "dev"]:
        splits[split] = read_jsonl(args.benchmark_dir / f"paper09_expanded_{split}.jsonl")
        pairs[split] = read_jsonl(args.benchmark_dir / f"paper09_expanded_{split}_ranking_pairs.jsonl")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    gate_train = [gate_record(r) for r in splits["train"]]
    gate_dev = [gate_record(r) for r in splits["dev"]]
    gate_train_balanced = balanced_gate_records(splits["train"], args.seed)
    ranker_train = [ranker_record(p, args.seed) for p in pairs["train"]]
    ranker_dev = [ranker_record(p, args.seed) for p in pairs["dev"]]
    ranker_train_pairs = [candidate_serialization_record(p) for p in pairs["train"]]
    ranker_dev_pairs = [candidate_serialization_record(p) for p in pairs["dev"]]

    write_jsonl(args.out_dir / "gate_train.jsonl", gate_train)
    write_jsonl(args.out_dir / "gate_dev.jsonl", gate_dev)
    write_jsonl(args.out_dir / "gate_train_balanced.jsonl", gate_train_balanced)
    write_jsonl(args.out_dir / "ranker_train.jsonl", ranker_train)
    write_jsonl(args.out_dir / "ranker_dev.jsonl", ranker_dev)
    write_jsonl(args.out_dir / "ranker_train_pairs.jsonl", ranker_train_pairs)
    write_jsonl(args.out_dir / "ranker_dev_pairs.jsonl", ranker_dev_pairs)

    summary = {
        "seed": args.seed,
        "source": str(args.benchmark_dir),
        "test_split_used": False,
        "gate": {
            "train": summarize_gate(gate_train),
            "train_balanced": summarize_gate(gate_train_balanced),
            "dev": summarize_gate(gate_dev),
        },
        "ranker": {
            "train": summarize_ranker(ranker_train),
            "dev": summarize_ranker(ranker_dev),
        },
    }
    write_summary(args.out_dir / "gate_ranker_summary.json", summary)
    write_readme(args.out_dir / "README.md", summary)


if __name__ == "__main__":
    main()
