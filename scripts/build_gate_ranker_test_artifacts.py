#!/usr/bin/env python3
"""Build Paper 09 gate/ranker artifacts for the frozen expanded test split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_gate_ranker_artifacts import (  # noqa: E402
    candidate_serialization_record,
    gate_record,
    ranker_record,
    read_jsonl,
    summarize_gate,
    summarize_ranker,
    write_jsonl,
    write_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260620)
    args = parser.parse_args()

    test_records = read_jsonl(args.benchmark_dir / "paper09_expanded_test.jsonl")
    test_pairs = read_jsonl(args.benchmark_dir / "paper09_expanded_test_ranking_pairs.jsonl")

    gate_test = [gate_record(record) for record in test_records]
    ranker_test = [ranker_record(pair, args.seed) for pair in test_pairs]
    ranker_test_pairs = [candidate_serialization_record(pair) for pair in test_pairs]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "gate_test.jsonl", gate_test)
    write_jsonl(args.out_dir / "ranker_test.jsonl", ranker_test)
    write_jsonl(args.out_dir / "ranker_test_pairs.jsonl", ranker_test_pairs)

    summary = {
        "seed": args.seed,
        "source": str(args.benchmark_dir),
        "test_split_used": True,
        "gate": {"test": summarize_gate(gate_test)},
        "ranker": {"test": summarize_ranker(ranker_test)},
    }
    write_summary(args.out_dir / "gate_ranker_test_summary.json", summary)
    (args.out_dir / "README.md").write_text(
        "# Paper 09 Final Test Gate/Ranker Artifacts\n\n"
        "These files are generated only for the frozen final test protocol.\n\n"
        "```json\n"
        + json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
