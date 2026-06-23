#!/usr/bin/env python3
"""Build a stratified human-audit packet for Paper 09 gold labels."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "runs" / "human_audit_packet_20260621"


SLICES = [
    ("recent_window", "temporal_recent_window", 40),
    ("previous_window", "temporal_previous_window", 40),
    ("unsupported_monthly_over_annual", "temporal_granularity_unanswerable", 40),
    ("future_city_unsupported", "stat_unanswerable", 40),
    ("mixed_change_ranking", "mixed_change_ranking", 40),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_sft_record(row: dict[str, Any]) -> dict[str, Any]:
    user = row["messages"][1]["content"]
    gold = json.loads(row["messages"][2]["content"])
    query = ""
    schema = []
    meta: dict[str, Any] = {}
    for line in user.splitlines():
        if line.startswith("Query:"):
            query = line.split(":", 1)[1].strip()
        elif line.startswith("name="):
            parts = {}
            for piece in line.split("|"):
                key, _, value = piece.strip().partition("=")
                parts[key] = value
            schema.append(parts)
        elif re.match(r"^(time_field|year_min|year_max|distinct_years|recent_10_start|recent_10_end|previous_10_start|previous_10_end|temporal_granularity|latest_year)=", line):
            key, value = line.split("=", 1)
            value = value.strip()
            if re.fullmatch(r"-?\d+", value):
                meta[key] = int(value)
            else:
                meta[key] = value
    return {
        "sample_id": row.get("sample_id"),
        "dataset_id": row.get("dataset_id"),
        "language": row.get("language"),
        "task_type": row.get("task_type"),
        "source": row.get("source", ""),
        "query": query,
        "schema": schema,
        "temporal_metadata": meta,
        "gold_intent": gold,
    }


def schema_text(schema: list[dict[str, Any]]) -> str:
    return " | ".join(
        f"{item.get('name','')}:{item.get('type','')}/{item.get('role','')}" for item in schema
    )


def select(rows: list[dict[str, Any]], task_type: str, limit: int) -> list[dict[str, Any]]:
    candidates = [row for row in rows if row.get("task_type") == task_type]
    candidates.sort(key=lambda row: (str(row.get("dataset_id", "")), str(row.get("language", "")), str(row.get("sample_id", ""))))
    selected = []
    seen_dataset_lang = set()
    for row in candidates:
        key = (row.get("dataset_id"), row.get("language"))
        if key in seen_dataset_lang:
            continue
        selected.append(row)
        seen_dataset_lang.add(key)
        if len(selected) >= limit:
            return selected
    for row in candidates:
        if row not in selected:
            selected.append(row)
            if len(selected) >= limit:
                break
    return selected


def select_diverse(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row.get("task_type", "")), []).append(row)
    for group in groups.values():
        group.sort(key=lambda row: (str(row.get("dataset_id", "")), str(row.get("sample_id", ""))))
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


def audit_row(audit_id: int, slice_name: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "audit_id": f"ha_{audit_id:03d}",
        "slice": slice_name,
        "sample_id": row.get("sample_id", ""),
        "dataset_id": row.get("dataset_id", ""),
        "source": row.get("source", ""),
        "language": row.get("language", ""),
        "task_type": row.get("task_type", ""),
        "query": row.get("query", ""),
        "schema_fields": schema_text(row.get("schema") or []),
        "temporal_metadata": json.dumps(row.get("temporal_metadata") or {}, ensure_ascii=False, sort_keys=True),
        "gold_intent": json.dumps(row.get("gold_intent") or {}, ensure_ascii=False, sort_keys=True),
        "human_answerability_correct": "",
        "human_intent_correct": "",
        "human_corrected_intent": "",
        "human_notes": "",
        "annotator_id": "",
    }


def append_slice(packet: list[dict[str, Any]], slice_name: str, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        packet.append(audit_row(len(packet) + 1, slice_name, row))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base = []
    for split in ["dev", "test"]:
        base.extend(read_jsonl(ROOT / "benchmark_expanded" / f"paper09_expanded_{split}.jsonl"))

    packet: list[dict[str, Any]] = []
    for slice_name, task_type, limit in SLICES:
        append_slice(packet, slice_name, select(base, task_type, limit))

    vi_rows = [parse_sft_record(row) for row in read_jsonl(ROOT / "benchmark_optional_audits" / "paper09_dev_vi_diacritic_sft.jsonl")]
    non_wb_rows = [parse_sft_record(row) for row in read_jsonl(ROOT / "benchmark_optional_audits" / "paper09_dev_non_worldbank_sft.jsonl")]
    append_slice(packet, "vietnamese_diacritic", select_diverse(vi_rows, 40))
    append_slice(packet, "non_worldbank_schema", select_diverse(non_wb_rows, 40))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "human_audit_packet_280.csv", packet)
    with (OUT_DIR / "human_audit_packet_280.jsonl").open("w", encoding="utf-8") as f:
        for row in packet:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "n": len(packet),
        "slices": {},
        "instructions": "Two annotators should independently mark human_answerability_correct and human_intent_correct as yes/no, add corrected intent JSON when no, then adjudicate disagreements.",
    }
    for row in packet:
        summary["slices"][row["slice"]] = summary["slices"].get(row["slice"], 0) + 1
    (OUT_DIR / "human_audit_packet_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "README.md").write_text(
        "# Paper 09 Human Gold-Label Audit Packet\n\n"
        "This packet contains 280 stratified records for human verification of automatically generated gold intents.\n\n"
        "Slices: recent-window, previous-window, unsupported monthly-over-annual, future/city unsupported, "
        "Vietnamese diacritic prompts, non-World-Bank schemas, and mixed change ranking.\n\n"
        "Recommended protocol: use two independent annotators. For each row, mark whether answerability is correct "
        "and whether the complete gold intent is correct. If not, provide a corrected JSON intent and notes. "
        "Report human verification accuracy and inter-annotator agreement before adjudication.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
