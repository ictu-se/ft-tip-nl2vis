#!/usr/bin/env python3
"""Create min/max-only temporal metadata SFT files for leakage ablation.

The full metadata SFT records include derived recent/previous temporal windows.
This converter keeps only runtime-observable support fields and removes those
candidate-window hints from the user prompt.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


KEEP_KEYS = [
    "time_field",
    "year_min",
    "year_max",
    "distinct_years",
    "temporal_granularity",
    "latest_year",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def parse_metadata_block(content: str) -> dict[str, str]:
    match = re.search(
        r"Temporal support metadata:\n(?P<body>.*?)\n\nInfer the temporal-statistical visualization intent\.",
        content,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("Could not locate temporal metadata block")
    metadata: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def replace_metadata_block(content: str) -> str:
    metadata = parse_metadata_block(content)
    minmax_text = "\n".join(f"{key}={metadata.get(key, '')}" for key in KEEP_KEYS)
    return re.sub(
        r"Temporal support metadata:\n.*?\n\nInfer the temporal-statistical visualization intent\.",
        "Temporal support metadata:\n"
        + minmax_text
        + "\n\nInfer the temporal-statistical visualization intent.",
        content,
        flags=re.DOTALL,
    )


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    converted = json.loads(json.dumps(record, ensure_ascii=False))
    messages = converted.get("messages", [])
    if len(messages) < 2 or messages[1].get("role") != "user":
        raise ValueError(f"Unexpected message format for {record.get('sample_id')}")
    messages[1]["content"] = replace_metadata_block(messages[1]["content"])
    converted["metadata_variant"] = "minmax_only"
    return converted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = read_jsonl(args.input)
    converted = [convert_record(record) for record in records]
    write_jsonl(args.output, converted)
    print(f"wrote {len(converted)} records to {args.output}")


if __name__ == "__main__":
    main()
