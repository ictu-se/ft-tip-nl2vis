#!/usr/bin/env python3
"""Analyze full-dev Paper 09 inference outputs by scientific error slices."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BOOL_METRICS = [
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

DEFAULT_RUNS = {
    "metadata_lora": "metadata_lora_full_dev/full_dev_outputs.jsonl",
    "unsupported_x4_lora": "unsupported_x4_lora_full_dev/full_dev_outputs.jsonl",
    "schema_only_lora": "schema_only_lora_full_dev/full_dev_outputs.jsonl",
    "qwen_prompt_only": "qwen_prompt_only_full_dev_if_time/full_dev_outputs.jsonl",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fieldnames:
        keys: list[str] = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if denominator == 0 else 100.0 * numerator / denominator


def normalize_filter(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "empty"
    if text == "all_years":
        return "all_years"
    if text == "latest_year":
        return "latest_year"
    if "-" in text:
        return "year_range"
    if text.isdigit():
        return "single_year"
    return "other"


def temporal_coverage(meta: dict[str, Any]) -> str:
    years = int(meta.get("distinct_years") or 0)
    if years <= 10:
        return "short_<=10"
    if years <= 25:
        return "medium_11_25"
    if years <= 50:
        return "long_26_50"
    return "very_long_>50"


def enrich_gold(row: dict[str, Any], dev_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dev = dev_by_id.get(str(row.get("sample_id")), {})
    gold = row.get("gold") or dev.get("gold_intent") or {}
    pred = row.get("prediction") or {}
    meta = dev.get("temporal_metadata") or {}
    enriched = dict(row)
    enriched.update(
        {
            "domain": dev.get("domain", ""),
            "dataset_title": dev.get("dataset_title", ""),
            "source": dev.get("source", ""),
            "gold_answerability": gold.get("answerability", ""),
            "pred_answerability": pred.get("answerability", "") if isinstance(pred, dict) else "",
            "gold_temporal_filter": gold.get("temporal_filter", ""),
            "pred_temporal_filter": pred.get("temporal_filter", "") if isinstance(pred, dict) else "",
            "gold_temporal_filter_type": normalize_filter(gold.get("temporal_filter")),
            "gold_temporal_granularity": gold.get("temporal_granularity", ""),
            "temporal_coverage": temporal_coverage(meta),
            "year_min": meta.get("year_min", ""),
            "year_max": meta.get("year_max", ""),
            "distinct_years": meta.get("distinct_years", ""),
            "query": dev.get("query", ""),
            "unsupported_reason": gold.get("unsupported_reason", ""),
        }
    )
    return enriched


def summarize_rows(rows: list[dict[str, Any]], prefix: dict[str, Any] | None = None) -> dict[str, Any]:
    out = dict(prefix or {})
    n = len(rows)
    out["n"] = n
    for key in BOOL_METRICS:
        out[f"{key}_pct"] = round(pct(sum(bool(r.get(key)) for r in rows), n), 4)
    out["required_field_f1"] = round(
        sum(float(r.get("required_field_f1") or 0.0) for r in rows) / n if n else 0.0,
        6,
    )
    out["false_plot_rate_pct"] = round(
        pct(
            sum(
                r.get("gold_answerability") == "unanswerable"
                and r.get("pred_answerability") == "answerable"
                for r in rows
            ),
            n,
        ),
        4,
    )
    out["over_refusal_rate_pct"] = round(
        pct(
            sum(
                r.get("gold_answerability") == "answerable"
                and r.get("pred_answerability") == "unanswerable"
                for r in rows
            ),
            n,
        ),
        4,
    )
    return out


def breakdown(rows: list[dict[str, Any]], run: str, key: str, min_n: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    out = []
    for value, group in groups.items():
        if len(group) >= min_n:
            out.append(summarize_rows(group, {"run": run, "slice": key, "value": value}))
    return sorted(out, key=lambda r: (r["slice"], -r["n"], r["value"]))


def failure_taxonomy(rows: list[dict[str, Any]], run: str) -> list[dict[str, Any]]:
    counters = Counter()
    for row in rows:
        gold_answerability = row.get("gold_answerability")
        pred_answerability = row.get("pred_answerability")
        if not row.get("json_ok"):
            counters["invalid_json"] += 1
        if gold_answerability == "unanswerable" and pred_answerability == "answerable":
            counters["false_plot_unanswerable_as_answerable"] += 1
        if gold_answerability == "answerable" and pred_answerability == "unanswerable":
            counters["over_refusal_answerable_as_unanswerable"] += 1
        if row.get("json_ok") and not row.get("task_type_ok"):
            counters["wrong_task_type"] += 1
        if row.get("json_ok") and not row.get("time_field_ok"):
            counters["wrong_time_field"] += 1
        if row.get("json_ok") and not row.get("measure_ok"):
            counters["wrong_measure"] += 1
        if row.get("json_ok") and not row.get("temporal_filter_ok"):
            counters["wrong_temporal_filter"] += 1
        if row.get("json_ok") and not row.get("statistic_ok"):
            counters["wrong_statistic"] += 1
        if row.get("json_ok") and row.get("core_intent_ok") and not row.get("full_intent_ok"):
            counters["core_ok_but_full_wrong"] += 1
    total = len(rows)
    return [
        {
            "run": run,
            "failure_type": key,
            "count": value,
            "rate_pct": round(pct(value, total), 4),
        }
        for key, value in counters.most_common()
    ]


def top_failures(rows: list[dict[str, Any]], run: str, group_key: str, limit: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key, ""))].append(row)
    out = []
    for value, group in groups.items():
        if len(group) < 5:
            continue
        failures = sum(not bool(r.get("full_intent_ok")) for r in group)
        out.append(
            {
                "run": run,
                "group": group_key,
                "value": value,
                "n": len(group),
                "full_failures": failures,
                "full_failure_rate_pct": round(pct(failures, len(group)), 4),
                "core_intent_ok_pct": round(pct(sum(bool(r.get("core_intent_ok")) for r in group), len(group)), 4),
                "temporal_filter_ok_pct": round(
                    pct(sum(bool(r.get("temporal_filter_ok")) for r in group), len(group)), 4
                ),
            }
        )
    return sorted(out, key=lambda r: (-r["full_failure_rate_pct"], -r["n"], r["value"]))[:limit]


def example_failures(rows: list[dict[str, Any]], run: str, limit_per_type: int) -> list[dict[str, Any]]:
    selected = []
    buckets: dict[str, int] = defaultdict(int)
    for row in rows:
        failure_types = []
        if row.get("gold_answerability") == "unanswerable" and row.get("pred_answerability") == "answerable":
            failure_types.append("false_plot")
        if row.get("gold_answerability") == "answerable" and row.get("pred_answerability") == "unanswerable":
            failure_types.append("over_refusal")
        if row.get("json_ok") and not row.get("temporal_filter_ok"):
            failure_types.append("wrong_temporal_filter")
        if row.get("json_ok") and not row.get("task_type_ok"):
            failure_types.append("wrong_task_type")
        if row.get("json_ok") and not row.get("measure_ok"):
            failure_types.append("wrong_measure")
        if not failure_types:
            continue
        for failure_type in failure_types:
            key = f"{run}:{failure_type}"
            if buckets[key] >= limit_per_type:
                continue
            pred = row.get("prediction") or {}
            gold = row.get("gold") or {}
            selected.append(
                {
                    "run": run,
                    "failure_type": failure_type,
                    "sample_id": row.get("sample_id"),
                    "dataset_id": row.get("dataset_id"),
                    "domain": row.get("domain"),
                    "language": row.get("language"),
                    "task_type": row.get("task_type"),
                    "query": row.get("query"),
                    "gold_answerability": gold.get("answerability", ""),
                    "pred_answerability": pred.get("answerability", "") if isinstance(pred, dict) else "",
                    "gold_temporal_filter": gold.get("temporal_filter", ""),
                    "pred_temporal_filter": pred.get("temporal_filter", "") if isinstance(pred, dict) else "",
                    "gold_measure": gold.get("measure", ""),
                    "pred_measure": pred.get("measure", "") if isinstance(pred, dict) else "",
                    "gold_task_type": gold.get("task_type", ""),
                    "pred_task_type": pred.get("task_type", "") if isinstance(pred, dict) else "",
                    "unsupported_reason": gold.get("unsupported_reason", ""),
                }
            )
            buckets[key] += 1
    return selected


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        cells = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = f"{value:.2f}"
            cells.append(str(value).replace("\n", " ")[:120])
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *body])


def write_report(
    path: Path,
    summaries: list[dict[str, Any]],
    taxonomies: list[dict[str, Any]],
    breakdown_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
) -> None:
    main_cols = [
        "run",
        "n",
        "json_ok_pct",
        "answerability_ok_pct",
        "temporal_filter_ok_pct",
        "core_intent_ok_pct",
        "full_intent_ok_pct",
        "false_plot_rate_pct",
        "over_refusal_rate_pct",
    ]
    taxonomy_cols = ["run", "failure_type", "count", "rate_pct"]
    slice_cols = [
        "run",
        "slice",
        "value",
        "n",
        "answerability_ok_pct",
        "temporal_filter_ok_pct",
        "core_intent_ok_pct",
        "full_intent_ok_pct",
    ]
    top_cols = [
        "run",
        "group",
        "value",
        "n",
        "full_failure_rate_pct",
        "core_intent_ok_pct",
        "temporal_filter_ok_pct",
    ]
    metadata_breakdowns = [
        r
        for r in breakdown_rows
        if r["run"] == "metadata_lora"
        and r["slice"]
        in {"language", "domain", "gold_answerability", "task_type", "gold_temporal_filter_type", "temporal_coverage"}
    ]
    text = [
        "# Paper 09 Full-Dev Error Analysis",
        "",
        "This report analyzes the expanded-dev split only. The held-out expanded test split remains untouched.",
        "",
        "## Overall Full-Dev Metrics",
        "",
        markdown_table(summaries, main_cols),
        "",
        "## Failure Taxonomy",
        "",
        markdown_table(taxonomies, taxonomy_cols),
        "",
        "## Metadata LoRA Slice Breakdown",
        "",
        markdown_table(metadata_breakdowns, slice_cols),
        "",
        "## Highest-Failure Groups",
        "",
        markdown_table(top_rows, top_cols),
        "",
        "## Modeling Implications",
        "",
        "- The metadata-aware LoRA remains the strongest current checkpoint on full-dev.",
        "- Schema-only performance confirms that explicit temporal support metadata carries model-relevant information.",
        "- Unsupported oversampling alone is not sufficient: it improves boundary behavior only weakly on full-dev and hurts temporal/core fidelity.",
        "- The next method should target answerability as a calibrated gate and temporal-filter choice as a hard-negative ranking problem, not as SFT-only generation.",
    ]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--min-slice-n", type=int, default=20)
    parser.add_argument("--examples-per-type", type=int, default=5)
    args = parser.parse_args()

    dev_rows = read_jsonl(args.dev)
    dev_by_id = {str(row["sample_id"]): row for row in dev_rows}
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    breakdown_rows = []
    taxonomy_rows = []
    top_rows = []
    example_rows = []

    for run_name, rel_path in DEFAULT_RUNS.items():
        output_path = args.run_root / rel_path
        if not output_path.exists():
            continue
        rows = [enrich_gold(row, dev_by_id) for row in read_jsonl(output_path)]
        summaries.append(summarize_rows(rows, {"run": run_name}))
        taxonomy_rows.extend(failure_taxonomy(rows, run_name))
        for key in [
            "language",
            "domain",
            "gold_answerability",
            "task_type",
            "gold_temporal_filter_type",
            "gold_temporal_granularity",
            "temporal_coverage",
            "source",
        ]:
            breakdown_rows.extend(breakdown(rows, run_name, key, args.min_slice_n))
        for group_key in ["dataset_id", "domain", "task_type", "gold_temporal_filter_type"]:
            top_rows.extend(top_failures(rows, run_name, group_key, limit=20))
        example_rows.extend(example_failures(rows, run_name, args.examples_per_type))

    summaries = sorted(summaries, key=lambda r: r["run"])
    breakdown_rows = sorted(
        breakdown_rows,
        key=lambda r: (r["run"], r["slice"], -r["n"], r["value"]),
    )
    taxonomy_rows = sorted(taxonomy_rows, key=lambda r: (r["run"], -r["count"], r["failure_type"]))
    top_rows = sorted(
        top_rows,
        key=lambda r: (r["run"], r["group"], -r["full_failure_rate_pct"], -r["n"], r["value"]),
    )

    write_csv(args.out_dir / "overall_summary.csv", summaries)
    write_csv(args.out_dir / "slice_breakdown.csv", breakdown_rows)
    write_csv(args.out_dir / "failure_taxonomy.csv", taxonomy_rows)
    write_csv(args.out_dir / "top_failure_groups.csv", top_rows)
    write_csv(args.out_dir / "representative_failures.csv", example_rows)
    write_report(
        args.out_dir / "FULL_DEV_ERROR_ANALYSIS.md",
        summaries,
        taxonomy_rows,
        breakdown_rows,
        top_rows[:80],
    )


if __name__ == "__main__":
    main()
