#!/usr/bin/env python3
"""Build swapped-order ranker evaluation records.

The original ranker dev records randomize whether the positive intent appears
as Candidate A or B. This script creates an anti-position-bias evaluation set by
swapping Candidate A and Candidate B for every record and flipping the gold
preferred label. It keeps the same pair ids with a suffix so resumed inference
does not collide with the original run.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


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


def flip_label(label: Any) -> str:
    text = str(label or "").strip().upper()
    if text.startswith("A"):
        return "B"
    if text.startswith("B"):
        return "A"
    raise ValueError(f"Cannot flip label: {label!r}")


def swap_candidate_blocks(text: str) -> str:
    pattern = re.compile(
        r"(Candidate A:\n)(?P<a>\{.*?\})(\n\nCandidate B:\n)(?P<b>\{.*?\})(\n\nChoose the candidate)",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("Could not locate Candidate A/B blocks")
    return (
        text[: match.start()]
        + match.group(1)
        + match.group("b")
        + match.group(3)
        + match.group("a")
        + match.group(5)
        + text[match.end() :]
    )


def swap_record(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out["pair_id"] = f"{record['pair_id']}_swapped"
    messages = [dict(message) for message in record["messages"]]
    messages[1]["content"] = swap_candidate_blocks(messages[1]["content"])
    gold = json.loads(messages[2]["content"])
    flipped = flip_label(gold.get("positive_label") or gold.get("preferred"))
    gold["preferred"] = flipped
    gold["positive_label"] = flipped
    messages[2]["content"] = json.dumps(gold, ensure_ascii=False, sort_keys=True)
    out["messages"] = messages
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    if args.limit is not None:
        rows = rows[: args.limit]
    write_jsonl(args.output, [swap_record(row) for row in rows])


if __name__ == "__main__":
    main()
