#!/usr/bin/env python3
"""Build grouped Paper 09 train/dev/test and SFT records.

This is deterministic infrastructure: it converts the Paper 08 TimeStat-NL2Vis
intent labels into instruction-tuning records without changing the labels.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


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


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}") from exc
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_intent(intent: dict) -> dict:
    return {key: intent.get(key) for key in INTENT_KEYS}


def schema_to_text(schema: list[dict]) -> str:
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


def to_sft_record(record: dict) -> dict:
    output = normalize_intent(record["gold_intent"])
    return {
        "sample_id": record["sample_id"],
        "dataset_id": record["dataset_id"],
        "language": record["language"],
        "task_type": record["task_type"],
        "answerability": record["answerability"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a temporal-statistical intent planner for NL2Vis. "
                    "Given a user query and dataset schema, output only valid "
                    "JSON matching the intent schema. Do not invent unsupported "
                    "fields or plot unanswerable requests."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Dataset title: {record.get('dataset_title', '')}\n"
                    f"Domain: {record.get('domain', '')}\n"
                    f"Language: {record.get('language', '')}\n"
                    f"Query: {record.get('query', '')}\n\n"
                    "Schema fields:\n"
                    f"{schema_to_text(record.get('schema', []))}\n\n"
                    "Infer the temporal-statistical visualization intent."
                ),
            },
            {
                "role": "assistant",
                "content": json.dumps(output, ensure_ascii=False, sort_keys=True),
            },
        ],
    }


def group_records(records: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[record["dataset_id"]].append(record)
    return groups


def assign_groups(
    groups: dict[str, list[dict]], train_ratio: float, dev_ratio: float, seed: int
) -> dict[str, str]:
    rng = random.Random(seed)
    group_items = list(groups.items())
    rng.shuffle(group_items)

    total = sum(len(records) for _, records in group_items)
    targets = {
        "train": total * train_ratio,
        "dev": total * dev_ratio,
        "test": total * (1.0 - train_ratio - dev_ratio),
    }
    counts = {"train": 0, "dev": 0, "test": 0}
    assignment: dict[str, str] = {}

    # Greedy balancing by absolute distance from target after assignment.
    for dataset_id, dataset_records in sorted(
        group_items, key=lambda item: len(item[1]), reverse=True
    ):
        size = len(dataset_records)
        split = min(
            counts,
            key=lambda name: abs((counts[name] + size) - targets[name])
            - abs(counts[name] - targets[name]),
        )
        assignment[dataset_id] = split
        counts[split] += size

    return assignment


def summarize(records: list[dict]) -> dict:
    return {
        "n": len(records),
        "datasets": len({record["dataset_id"] for record in records}),
        "language": dict(Counter(record["language"] for record in records)),
        "answerability": dict(Counter(record["answerability"] for record in records)),
        "task_type": dict(Counter(record["task_type"] for record in records)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "manuscripts/08_temporal_statistical_intent_nl2vis/benchmark/"
            "temporal_stat_tasks.jsonl"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("manuscripts/09_finetuned_temporal_intent_planner_nl2vis/benchmark"),
    )
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--dev-ratio", type=float, default=0.15)
    args = parser.parse_args()

    records = read_jsonl(args.source)
    groups = group_records(records)
    assignment = assign_groups(groups, args.train_ratio, args.dev_ratio, args.seed)

    splits = {"train": [], "dev": [], "test": []}
    for record in records:
        splits[assignment[record["dataset_id"]]].append(record)

    for split_name, split_records in splits.items():
        split_records.sort(key=lambda record: record["sample_id"])
        write_jsonl(args.out_dir / f"paper09_{split_name}.jsonl", split_records)
        write_jsonl(
            args.out_dir / f"paper09_{split_name}_sft.jsonl",
            [to_sft_record(record) for record in split_records],
        )

    summary = {
        "source": str(args.source),
        "seed": args.seed,
        "split_policy": "grouped_by_dataset_id",
        "splits": {name: summarize(split_records) for name, split_records in splits.items()},
    }
    (args.out_dir / "paper09_split_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
