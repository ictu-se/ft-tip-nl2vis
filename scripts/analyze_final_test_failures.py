#!/usr/bin/env python3
"""Analyze frozen Paper 09 final-test failures."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BOOL_KEYS = [
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def pct(num: int | float, den: int | float) -> float:
    return 100.0 * num / den if den else 0.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    out = {"n": n}
    for key in BOOL_KEYS:
        out[f"{key}_pct"] = round(pct(sum(bool(row.get(key)) for row in rows), n), 4)
    out["false_plot_rate_pct"] = round(
        pct(
            sum(
                (row.get("gold") or {}).get("answerability") == "unanswerable"
                and (row.get("prediction") or {}).get("answerability") == "answerable"
                for row in rows
            ),
            n,
        ),
        4,
    )
    out["over_refusal_rate_pct"] = round(
        pct(
            sum(
                (row.get("gold") or {}).get("answerability") == "answerable"
                and (row.get("prediction") or {}).get("answerability") == "unanswerable"
                for row in rows
            ),
            n,
        ),
        4,
    )
    return out


def enrich_policy(row: dict[str, Any], records_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sample_id = str(row.get("sample_id"))
    record = records_by_id.get(sample_id, {})
    gold = row.get("gold") or {}
    pred = row.get("prediction") or {}
    meta = record.get("temporal_metadata") or {}
    return {
        **row,
        "domain": record.get("domain", ""),
        "source": record.get("source", ""),
        "dataset_title": record.get("dataset_title", ""),
        "query": record.get("query", ""),
        "gold_answerability": gold.get("answerability", ""),
        "pred_answerability": pred.get("answerability", "") if isinstance(pred, dict) else "",
        "gold_temporal_filter": gold.get("temporal_filter", ""),
        "pred_temporal_filter": pred.get("temporal_filter", "") if isinstance(pred, dict) else "",
        "year_min": meta.get("year_min", ""),
        "year_max": meta.get("year_max", ""),
        "distinct_years": meta.get("distinct_years", ""),
    }


def policy_taxonomy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters = Counter()
    for row in rows:
        gold = row.get("gold") or {}
        pred = row.get("prediction") or {}
        if not row.get("json_ok"):
            counters["invalid_json"] += 1
        if gold.get("answerability") == "unanswerable" and pred.get("answerability") == "answerable":
            counters["false_plot"] += 1
        if gold.get("answerability") == "answerable" and pred.get("answerability") == "unanswerable":
            counters["over_refusal"] += 1
        for key, name in [
            ("task_type_ok", "wrong_task_type"),
            ("time_field_ok", "wrong_time_field"),
            ("measure_ok", "wrong_measure"),
            ("temporal_filter_ok", "wrong_temporal_filter"),
            ("statistic_ok", "wrong_statistic"),
        ]:
            if row.get("json_ok") and not row.get(key):
                counters[name] += 1
        if row.get("core_intent_ok") and not row.get("full_intent_ok"):
            counters["core_ok_but_full_wrong"] += 1
    n = len(rows)
    return [
        {"failure_type": key, "count": value, "rate_pct": round(pct(value, n), 4)}
        for key, value in counters.most_common()
    ]


def breakdown(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    out = []
    for value, group in groups.items():
        item = summarize(group)
        item["slice"] = key
        item["value"] = value
        out.append(item)
    return sorted(out, key=lambda row: (-row["n"], row["value"]))


def representative_policy_failures(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    failures = [row for row in rows if not row.get("full_intent_ok")]
    selected = []
    seen_types = Counter()
    for row in failures:
        types = []
        if not row.get("answerability_ok"):
            types.append("answerability")
        if not row.get("task_type_ok"):
            types.append("task_type")
        if not row.get("temporal_filter_ok"):
            types.append("temporal_filter")
        if not row.get("measure_ok"):
            types.append("measure")
        if not row.get("statistic_ok"):
            types.append("statistic")
        if not types:
            types = ["full_only"]
        main_type = types[0]
        if seen_types[main_type] >= 4:
            continue
        seen_types[main_type] += 1
        gold = row.get("gold") or {}
        pred = row.get("prediction") or {}
        selected.append(
            {
                "failure_type": main_type,
                "sample_id": row.get("sample_id"),
                "dataset_id": row.get("dataset_id"),
                "language": row.get("language"),
                "task_type": row.get("task_type"),
                "query": row.get("query"),
                "gold_answerability": gold.get("answerability", ""),
                "pred_answerability": pred.get("answerability", ""),
                "gold_temporal_filter": gold.get("temporal_filter", ""),
                "pred_temporal_filter": pred.get("temporal_filter", ""),
                "gold_task_type": gold.get("task_type", ""),
                "pred_task_type": pred.get("task_type", ""),
                "gold_measure": gold.get("measure", ""),
                "pred_measure": pred.get("measure", ""),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def ranker_sensitivity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("task_type", ""))].append(row)
    out = []
    for task, group in groups.items():
        out.append(
            {
                "task_type": task,
                "n": len(group),
                "consistent_pct": round(pct(sum(bool(r.get("symmetric_consistent")) for r in group), len(group)), 4),
                "symmetric_ok_pct": round(pct(sum(bool(r.get("symmetric_pairwise_ok")) for r in group), len(group)), 4),
                "fallback_pct": round(pct(sum(not bool(r.get("symmetric_consistent")) for r in group), len(group)), 4),
            }
        )
    return sorted(out, key=lambda row: (-row["fallback_pct"], row["task_type"]))


def write_markdown(
    path: Path,
    policy_summary: dict[str, Any],
    taxonomy: list[dict[str, Any]],
    task_breakdown: list[dict[str, Any]],
    ranker_breakdown: list[dict[str, Any]],
    examples: list[dict[str, Any]],
) -> None:
    lines = [
        "# Paper 09 Final-Test Failure Analysis",
        "",
        "This analysis is performed after the frozen one-time expanded-test run. It does not change the method.",
        "",
        "## Policy Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| n | {policy_summary['n']} |",
        f"| Core-intent accuracy | {policy_summary['core_intent_ok_pct']:.2f}% |",
        f"| Full-intent accuracy | {policy_summary['full_intent_ok_pct']:.2f}% |",
        f"| Answerability accuracy | {policy_summary['answerability_ok_pct']:.2f}% |",
        f"| Temporal-filter accuracy | {policy_summary['temporal_filter_ok_pct']:.2f}% |",
        f"| False-plot rate | {policy_summary['false_plot_rate_pct']:.2f}% |",
        f"| Over-refusal rate | {policy_summary['over_refusal_rate_pct']:.2f}% |",
        "",
        "## Dominant Policy Failure Types",
        "",
        "| Failure type | Count | Rate |",
        "| --- | ---: | ---: |",
    ]
    for row in taxonomy[:10]:
        lines.append(f"| {row['failure_type']} | {row['count']} | {row['rate_pct']:.2f}% |")
    lines += [
        "",
        "## Task-Type Policy Slices",
        "",
        "| Task type | n | Full | Core | Temporal filter | Answerability |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted([r for r in task_breakdown if r["slice"] == "task_type"], key=lambda r: r["value"]):
        lines.append(
            f"| {row['value']} | {row['n']} | {row['full_intent_ok_pct']:.2f}% | "
            f"{row['core_intent_ok_pct']:.2f}% | {row['temporal_filter_ok_pct']:.2f}% | "
            f"{row['answerability_ok_pct']:.2f}% |"
        )
    lines += [
        "",
        "## Ranker Symmetric-Policy Sensitivity",
        "",
        "| Task type | n | Symmetric correct | Fallback/order-sensitive |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in ranker_breakdown:
        lines.append(f"| {row['task_type']} | {row['n']} | {row['symmetric_ok_pct']:.2f}% | {row['fallback_pct']:.2f}% |")
    lines += [
        "",
        "## Representative Policy Failures",
        "",
        "| Type | Sample | Task | Lang | Gold filter | Pred filter | Query |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in examples[:12]:
        query = str(row.get("query", "")).replace("|", "/")[:140]
        lines.append(
            f"| {row['failure_type']} | {row['sample_id']} | {row['task_type']} | {row['language']} | "
            f"{row['gold_temporal_filter']} | {row['pred_temporal_filter']} | {query} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-records", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--symmetric-ranker-pairs", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    records_by_id = {str(row["sample_id"]): row for row in read_jsonl(args.test_records)}
    policy_rows = [enrich_policy(row, records_by_id) for row in read_jsonl(args.policy)]
    ranker_rows = read_jsonl(args.symmetric_ranker_pairs)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    policy_summary = summarize(policy_rows)
    taxonomy = policy_taxonomy(policy_rows)
    task_breakdown = breakdown(policy_rows, "task_type")
    language_breakdown = breakdown(policy_rows, "language")
    ranker_breakdown = ranker_sensitivity(ranker_rows)
    examples = representative_policy_failures(policy_rows)

    (args.out_dir / "final_test_failure_summary.json").write_text(
        json.dumps(
            {
                "policy_summary": policy_summary,
                "policy_taxonomy": taxonomy,
                "ranker_task_sensitivity": ranker_breakdown,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_csv(args.out_dir / "policy_failure_taxonomy.csv", taxonomy)
    write_csv(args.out_dir / "policy_task_breakdown.csv", task_breakdown)
    write_csv(args.out_dir / "policy_language_breakdown.csv", language_breakdown)
    write_csv(args.out_dir / "ranker_task_sensitivity.csv", ranker_breakdown)
    write_csv(args.out_dir / "representative_policy_failures.csv", examples)
    write_markdown(args.out_dir / "FINAL_TEST_FAILURE_ANALYSIS.md", policy_summary, taxonomy, task_breakdown, ranker_breakdown, examples)


if __name__ == "__main__":
    main()
