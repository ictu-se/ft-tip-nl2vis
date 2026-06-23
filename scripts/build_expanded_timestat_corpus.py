#!/usr/bin/env python3
"""Build the expanded Paper 09 temporal-intent corpus from local datasets.

This script is deterministic infrastructure. It inspects local CSV files,
derives temporal support metadata, creates gold temporal/statistical intent
plans, and writes grouped train/dev/test splits. No model-generated labels are
created here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "manuscripts" / "09_finetuned_temporal_intent_planner_nl2vis"
DATA_ROOT = ROOT / "data_benchmarks" / "benchmark"
META_PATH = DATA_ROOT / "metadata" / "datasets.json"
OUT = PAPER / "benchmark_expanded"

COUNTRY_VALUES = ["Vietnam", "Thailand", "Indonesia", "Malaysia", "Philippines"]

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


def stable_index(text: str, modulo: int) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % modulo


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fields_by_role(dataset: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for col in dataset.get("columns", []):
        role = str(col.get("role", ""))
        typ = str(col.get("type", ""))
        name = str(col.get("name", ""))
        if role and name:
            out[role].append(name)
        if typ and name:
            out[typ].append(name)
    return out


def compact_schema(dataset: dict[str, Any]) -> list[dict[str, str]]:
    schema = []
    for col in dataset.get("columns", []):
        schema.append(
            {
                "name": str(col.get("name", "")),
                "type": str(col.get("type", "")),
                "role": str(col.get("role", "")),
                "unit": str(col.get("unit", "")),
                "description_vi": str(col.get("description_vi", "")),
            }
        )
    return schema


def measure_label(dataset: dict[str, Any], measure: str) -> str:
    for col in dataset.get("columns", []):
        if col.get("name") == measure:
            desc = str(col.get("description_vi") or "").strip()
            if desc and desc.isascii():
                return desc
    return measure.replace("_", " ")


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        value_float = float(text.replace(",", ""))
    except ValueError:
        return None
    if math.isnan(value_float) or math.isinf(value_float):
        return None
    return value_float


def inspect_csv(dataset: dict[str, Any], csv_path: Path) -> dict[str, Any]:
    roles = fields_by_role(dataset)
    time_field = roles.get("time", [""])[0]
    measures = roles.get("measure", [])
    dimensions = roles.get("dimension", [])
    years: list[int] = []
    measure_nonmissing = Counter()
    measure_total = Counter()
    dimension_values: dict[str, set[str]] = {dim: set() for dim in dimensions}
    rows = 0

    if not csv_path.exists() or not time_field or not measures:
        return {
            "csv_exists": csv_path.exists(),
            "usable": False,
            "reason": "missing_csv_or_required_roles",
        }

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = set(reader.fieldnames or [])
        missing_cols = [c for c in [time_field, *measures, *dimensions] if c not in columns]
        if missing_cols:
            return {
                "csv_exists": True,
                "usable": False,
                "reason": "missing_columns:" + ",".join(missing_cols),
            }
        for row in reader:
            rows += 1
            year_value = parse_number(row.get(time_field))
            if year_value is not None:
                years.append(int(year_value))
            for measure in measures:
                measure_total[measure] += 1
                if parse_number(row.get(measure)) is not None:
                    measure_nonmissing[measure] += 1
            for dim in dimensions:
                value = str(row.get(dim, "")).strip()
                if value:
                    dimension_values[dim].add(value)

    if not years:
        return {"csv_exists": True, "usable": False, "reason": "no_valid_years"}

    year_min = min(years)
    year_max = max(years)
    distinct_years = len(set(years))
    primary_measure = measures[0]
    total = measure_total[primary_measure]
    nonmissing = measure_nonmissing[primary_measure]
    if total == 0 or nonmissing == 0:
        return {"csv_exists": True, "usable": False, "reason": "no_measure_values"}

    return {
        "csv_exists": True,
        "usable": True,
        "reason": "",
        "row_count_actual": rows,
        "year_min_actual": year_min,
        "year_max_actual": year_max,
        "distinct_years": distinct_years,
        "measure_missing_ratio": round(1.0 - (nonmissing / total), 6),
        "dimension_cardinality": {k: len(v) for k, v in dimension_values.items()},
    }


def temporal_metadata(dataset: dict[str, Any], csv_info: dict[str, Any]) -> dict[str, Any]:
    ymin = int(csv_info["year_min_actual"])
    ymax = int(csv_info["year_max_actual"])
    recent_start = max(ymin, ymax - 9)
    prev_end = max(ymin, recent_start - 1)
    prev_start = max(ymin, prev_end - 9)
    return {
        "time_field": fields_by_role(dataset)["time"][0],
        "year_min": ymin,
        "year_max": ymax,
        "distinct_years": int(csv_info["distinct_years"]),
        "recent_10_start": recent_start,
        "recent_10_end": ymax,
        "previous_10_start": prev_start,
        "previous_10_end": prev_end,
        "temporal_granularity": "year",
        "latest_year": ymax,
    }


def base_gold(
    dataset: dict[str, Any],
    csv_info: dict[str, Any],
    task_type: str,
    language: str,
    query: str,
    chart_type: str,
    temporal_filter: str,
    statistic: str,
    aggregation: str,
    *,
    top_k: int | None = None,
    answerability: str = "answerable",
    unsupported_reason: str = "",
    secondary_measure: str = "",
) -> dict[str, Any]:
    roles = fields_by_role(dataset)
    measure = roles["measure"][0]
    time_field = roles["time"][0]
    group_by = "country" if "country" in roles.get("dimension", []) else roles["dimension"][0]
    required = [time_field, measure, group_by]
    if secondary_measure:
        required.append(secondary_measure)
    return {
        "sample_id": "",
        "dataset_id": dataset["dataset_id"],
        "dataset_title": dataset.get("title", ""),
        "domain": dataset.get("domain", ""),
        "source": dataset.get("source", ""),
        "language": language,
        "query": query,
        "task_type": task_type,
        "answerability": answerability,
        "schema": compact_schema(dataset),
        "temporal_metadata": temporal_metadata(dataset, csv_info),
        "gold_intent": {
            "answerability": answerability,
            "task_type": task_type,
            "required_fields": sorted(set(required)) if answerability == "answerable" else [],
            "time_field": time_field if answerability == "answerable" else "",
            "measure": measure if answerability == "answerable" else "",
            "secondary_measure": secondary_measure,
            "group_by": group_by if answerability == "answerable" else "",
            "chart_type": chart_type if answerability == "answerable" else "none",
            "temporal_filter": temporal_filter,
            "temporal_granularity": "year",
            "statistic": statistic,
            "aggregation": aggregation,
            "sort": "descending"
            if task_type in {"stat_ranking_topk", "mixed_temporal_ranking", "mixed_change_ranking"}
            else "none",
            "top_k": top_k,
            "unsupported_reason": unsupported_reason,
        },
    }


def make_tasks_for_dataset(dataset: dict[str, Any], csv_info: dict[str, Any]) -> list[dict[str, Any]]:
    roles = fields_by_role(dataset)
    measures = roles["measure"]
    measure = measures[0]
    group = "country" if "country" in roles.get("dimension", []) else roles["dimension"][0]
    label = measure_label(dataset, measure)
    tm = temporal_metadata(dataset, csv_info)
    ymin = tm["year_min"]
    ymax = tm["year_max"]
    mid = ymin + max(1, (ymax - ymin) // 2)
    start = tm["recent_10_start"]
    prev_start = tm["previous_10_start"]
    prev_end = tm["previous_10_end"]
    country = COUNTRY_VALUES[stable_index(dataset["dataset_id"], len(COUNTRY_VALUES))]

    tasks = [
        base_gold(dataset, csv_info, "temporal_trend", "en", f"Show the trend of {label} in {country} over time.", "line", "all_years", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_period_filter", "en", f"Compare {label} by {group} from {start} to {ymax}.", "bar", f"{start}-{ymax}", "comparison", "none"),
        base_gold(dataset, csv_info, "temporal_recent_window", "en", f"Show the most recent 10-year pattern of {label} for {country}.", "line", f"last_10_years:{start}-{ymax}", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_previous_window", "en", f"Show the previous decade before the latest window for {label} in {country}.", "line", f"previous_10_years:{prev_start}-{prev_end}", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_before_after", "en", f"Compare average {label} before and after {mid}.", "bar", f"before_after:{mid}", "mean", "mean"),
        base_gold(dataset, csv_info, "stat_ranking_topk", "en", f"Rank the top 5 countries by latest {label}.", "bar", "latest_year", "top_k", "none", top_k=5),
        base_gold(dataset, csv_info, "stat_distribution", "en", f"Show the distribution of {label} across countries and years.", "boxplot", "all_years", "distribution", "none"),
        base_gold(dataset, csv_info, "stat_average_period", "en", f"Show the average {label} by country during {start}-{ymax}.", "bar", f"{start}-{ymax}", "mean", "mean"),
        base_gold(dataset, csv_info, "stat_change", "en", f"Show the change in {label} from {start} to {ymax} by country.", "bar", f"{start}_to_{ymax}", "difference", "none"),
        base_gold(dataset, csv_info, "stat_outlier", "en", f"Find unusually high or low observations of {label}.", "point", "all_years", "outlier", "none"),
        base_gold(dataset, csv_info, "mixed_temporal_ranking", "en", f"Which countries have the highest {label} in the latest year?", "bar", "latest_year", "top_k", "none", top_k=5),
        base_gold(dataset, csv_info, "mixed_temporal_distribution", "en", f"Show the distribution of {label} in {ymax}.", "boxplot", f"year:{ymax}", "distribution", "none"),
        base_gold(dataset, csv_info, "mixed_change_ranking", "en", f"Rank countries by growth in {label} over the last decade.", "bar", f"{start}_to_{ymax}", "difference_top_k", "none", top_k=5),
        base_gold(dataset, csv_info, "temporal_boundary_check", "en", f"Use the exact data boundary to plot {label} from the first available year to the latest year.", "line", f"{ymin}-{ymax}", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_granularity_unanswerable", "en", f"Show monthly {label} trends for {country}.", "none", "monthly", "trend", "none", answerability="unanswerable", unsupported_reason="monthly granularity is not available; schema has annual year values"),
        base_gold(dataset, csv_info, "stat_unanswerable", "en", f"Show the forecasted {label} for next year by city.", "none", "future", "forecast", "none", answerability="unanswerable", unsupported_reason="forecast and city fields are not available"),
        base_gold(dataset, csv_info, "temporal_trend", "vi", f"Ve xu huong {label} cua {country} theo nam.", "line", "all_years", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_period_filter", "vi", f"So sanh {label} theo {group} trong giai doan {start}-{ymax}.", "bar", f"{start}-{ymax}", "comparison", "none"),
        base_gold(dataset, csv_info, "temporal_recent_window", "vi", f"Cho toi bieu do 10 nam gan nhat cua {label} o {country}.", "line", f"last_10_years:{start}-{ymax}", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_previous_window", "vi", f"Ve thap ky lien truoc cua {label} truoc giai doan moi nhat.", "line", f"previous_10_years:{prev_start}-{prev_end}", "trend", "none"),
        base_gold(dataset, csv_info, "stat_ranking_topk", "vi", f"Xep hang 5 nuoc cao nhat theo {label} moi nhat.", "bar", "latest_year", "top_k", "none", top_k=5),
        base_gold(dataset, csv_info, "stat_average_period", "vi", f"Tinh trung binh {label} theo quoc gia trong giai doan {start}-{ymax}.", "bar", f"{start}-{ymax}", "mean", "mean"),
        base_gold(dataset, csv_info, "stat_change", "vi", f"Ve muc thay doi {label} tu {start} den {ymax} theo quoc gia.", "bar", f"{start}_to_{ymax}", "difference", "none"),
        base_gold(dataset, csv_info, "mixed_temporal_ranking", "vi", f"Nuoc nao co {label} cao nhat trong nam moi nhat?", "bar", "latest_year", "top_k", "none", top_k=5),
        base_gold(dataset, csv_info, "temporal_boundary_check", "vi", f"Dung dung mien nam co trong du lieu de ve {label} tu nam dau tien den nam moi nhat.", "line", f"{ymin}-{ymax}", "trend", "none"),
        base_gold(dataset, csv_info, "temporal_granularity_unanswerable", "vi", f"Ve xu huong hang thang cua {label} cho {country}.", "none", "monthly", "trend", "none", answerability="unanswerable", unsupported_reason="monthly granularity is not available; schema has annual year values"),
        base_gold(dataset, csv_info, "stat_unanswerable", "vi", f"Du bao {label} nam sau theo thanh pho.", "none", "future", "forecast", "none", answerability="unanswerable", unsupported_reason="forecast and city fields are not available"),
    ]

    if len(measures) >= 2:
        second = measures[1]
        tasks.extend(
            [
                base_gold(dataset, csv_info, "stat_correlation_proxy", "en", f"Show the relationship between {measure} and {second} in {ymax}.", "scatter", f"year:{ymax}", "correlation", "none", secondary_measure=second),
                base_gold(dataset, csv_info, "stat_correlation_proxy", "vi", f"Ve moi quan he giua {measure} va {second} trong nam {ymax}.", "scatter", f"year:{ymax}", "correlation", "none", secondary_measure=second),
            ]
        )

    return tasks


def wrong_temporal_filters(intent: dict[str, Any], tm: dict[str, Any]) -> list[str]:
    gold = str(intent.get("temporal_filter", ""))
    ymin = int(tm["year_min"])
    ymax = int(tm["year_max"])
    recent_start = int(tm["recent_10_start"])
    candidates = [
        "2015-2024",
        f"last_10_years:{max(ymin, recent_start - 1)}-{max(ymin, ymax - 1)}",
        f"last_10_years:{max(ymin, recent_start - 10)}-{max(ymin, ymax - 10)}",
        f"{max(ymin, recent_start - 1)}-{ymax}",
        f"{ymax + 1}-{ymax + 10}",
        "monthly",
    ]
    return [candidate for candidate in candidates if candidate != gold]


def make_ranking_pairs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    temporal_types = {
        "temporal_period_filter",
        "temporal_recent_window",
        "temporal_previous_window",
        "temporal_boundary_check",
        "stat_average_period",
        "stat_change",
        "mixed_change_ranking",
    }
    for record in records:
        if record["answerability"] != "answerable" or record["task_type"] not in temporal_types:
            continue
        gold = normalize_intent(record["gold_intent"])
        for idx, bad_filter in enumerate(wrong_temporal_filters(gold, record["temporal_metadata"]), start=1):
            negative = dict(gold)
            negative["temporal_filter"] = bad_filter
            pairs.append(
                {
                    "pair_id": f"{record['sample_id']}_hn{idx}",
                    "sample_id": record["sample_id"],
                    "dataset_id": record["dataset_id"],
                    "language": record["language"],
                    "task_type": record["task_type"],
                    "query": record["query"],
                    "schema": record["schema"],
                    "temporal_metadata": record["temporal_metadata"],
                    "positive_intent": gold,
                    "negative_intent": negative,
                    "hard_negative_type": "temporal_boundary_or_window_mismatch",
                }
            )
    return pairs


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


def to_sft_record(record: dict[str, Any], *, include_temporal_metadata: bool) -> dict[str, Any]:
    metadata_block = ""
    if include_temporal_metadata:
        metadata_block = "\nTemporal support metadata:\n" + temporal_metadata_to_text(record["temporal_metadata"]) + "\n"
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
                    "You are a temporal-grounding-aware intent planner for NL2Vis. "
                    "Given a user query, dataset schema, and optional temporal support "
                    "metadata, output only valid JSON matching the intent schema. "
                    "Never invent fields, temporal ranges, or unavailable granularities."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Dataset title: {record.get('dataset_title', '')}\n"
                    f"Domain: {record.get('domain', '')}\n"
                    f"Source: {record.get('source', '')}\n"
                    f"Language: {record.get('language', '')}\n"
                    f"Query: {record.get('query', '')}\n\n"
                    "Schema fields:\n"
                    f"{schema_to_text(record.get('schema', []))}\n"
                    f"{metadata_block}\n"
                    "Infer the temporal-statistical visualization intent."
                ),
            },
            {
                "role": "assistant",
                "content": json.dumps(normalize_intent(record["gold_intent"]), ensure_ascii=False, sort_keys=True),
            },
        ],
    }


def group_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record["dataset_id"]].append(record)
    return groups


def split_groups(
    datasets: list[dict[str, Any]],
    groups: dict[str, list[dict[str, Any]]],
    *,
    train_ratio: float,
    dev_ratio: float,
    seed: int,
) -> dict[str, str]:
    by_dataset = {d["dataset_id"]: d for d in datasets}
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for dataset_id in groups:
        d = by_dataset[dataset_id]
        year_max = int(d["temporal_metadata"]["year_max"])
        year_bucket = "recent" if year_max >= 2023 else "older"
        buckets[(str(d.get("domain", "")), year_bucket)].append(dataset_id)

    rng = random.Random(seed)
    assignment: dict[str, str] = {}
    for _, ids in sorted(buckets.items(), key=lambda item: str(item[0])):
        rng.shuffle(ids)
        n = len(ids)
        if n == 1:
            n_train, n_dev = 1, 0
        elif n == 2:
            n_train, n_dev = 1, 1
        else:
            n_train = max(1, round(n * train_ratio))
            n_dev = max(1, round(n * dev_ratio))
            if n_train + n_dev >= n:
                n_train = max(1, n - 2)
                n_dev = 1
        for dataset_id in ids[:n_train]:
            assignment[dataset_id] = "train"
        for dataset_id in ids[n_train : n_train + n_dev]:
            assignment[dataset_id] = "dev"
        for dataset_id in ids[n_train + n_dev :]:
            assignment[dataset_id] = "test"

    return assignment


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n": len(records),
        "datasets": len({r["dataset_id"] for r in records}),
        "language": dict(Counter(r["language"] for r in records)),
        "answerability": dict(Counter(r["answerability"] for r in records)),
        "task_type": dict(Counter(r["task_type"] for r in records)),
        "domain": dict(Counter(r["domain"] for r in records)),
        "year_max": dict(Counter(str(r["temporal_metadata"]["year_max"]) for r in records)),
    }


def write_summary(
    path: Path,
    *,
    records: list[dict[str, Any]],
    inventory: list[dict[str, Any]],
    splits: dict[str, list[dict[str, Any]]],
    ranking_pairs: dict[str, list[dict[str, Any]]],
) -> None:
    by_domain = Counter(r["domain"] for r in records)
    by_source = Counter(r["source"] for r in records)
    lines = [
        "# Expanded Paper 09 TimeStat Corpus",
        "",
        "This corpus is generated from local CSV files and dataset metadata. It is intended for the serious Paper 09 ablation plan: schema-only SFT, temporal-metadata-aware SFT, and hard-negative temporal ranking.",
        "",
        "## Corpus Size",
        "",
        f"- Inventoried metadata datasets: {len(inventory)}",
        f"- Usable datasets: {len({r['dataset_id'] for r in records})}",
        f"- Intent records: {len(records)}",
        f"- Hard-negative ranking pairs: {sum(len(v) for v in ranking_pairs.values())}",
        "",
        "## Split Summary",
        "",
    ]
    for name in ["train", "dev", "test"]:
        split = splits[name]
        lines.append(f"- {name}: {len(split)} records, {len({r['dataset_id'] for r in split})} datasets")
    lines.extend(["", "## Top Domains", ""])
    lines.extend(f"- {domain}: {count}" for domain, count in by_domain.most_common(15))
    lines.extend(["", "## Sources", ""])
    lines.extend(f"- {source}: {count}" for source, count in by_source.most_common())
    lines.extend(
        [
            "",
            "## Scientific Use",
            "",
            "- Use `*_schema_only_sft.jsonl` to test whether the model can infer temporal bounds from schema alone.",
            "- Use `*_with_temporal_metadata_sft.jsonl` to test the proposed temporal-grounding-aware planner.",
            "- Use `*_ranking_pairs.jsonl` for the hard-negative objective and ablation of temporal-boundary reasoning.",
            "- Keep the expanded test split untouched until the training and checkpoint-selection protocol is frozen.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--dev-ratio", type=float, default=0.15)
    args = parser.parse_args()

    metadata = read_json(META_PATH)
    inventory: list[dict[str, Any]] = []
    usable: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for dataset in metadata:
        roles = fields_by_role(dataset)
        csv_path = DATA_ROOT / str(dataset.get("csv_path", ""))
        csv_info = inspect_csv(dataset, csv_path)
        item = {
            "dataset_id": dataset.get("dataset_id", ""),
            "title": dataset.get("title", ""),
            "domain": dataset.get("domain", ""),
            "source": dataset.get("source", ""),
            "csv_path": str(dataset.get("csv_path", "")),
            "has_time": bool(roles.get("time")),
            "has_measure": bool(roles.get("measure")),
            "has_dimension": bool(roles.get("dimension")),
            **csv_info,
        }
        inventory.append(item)
        if not (roles.get("time") and roles.get("measure") and roles.get("dimension")):
            continue
        if not csv_info.get("usable"):
            continue
        enriched = dict(dataset)
        enriched["temporal_metadata"] = temporal_metadata(dataset, csv_info)
        usable.append(enriched)
        records.extend(make_tasks_for_dataset(dataset, csv_info))

    for idx, record in enumerate(records, start=1):
        record["sample_id"] = f"paper09x_{idx:06d}"

    groups = group_records(records)
    assignment = split_groups(
        usable,
        groups,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
        seed=args.seed,
    )
    splits = {"train": [], "dev": [], "test": []}
    for record in records:
        splits[assignment[record["dataset_id"]]].append(record)
    for split_records in splits.values():
        split_records.sort(key=lambda row: row["sample_id"])

    ranking_pairs = {name: make_ranking_pairs(split_records) for name, split_records in splits.items()}

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "EXPANDED_DATASET_INVENTORY.csv", inventory)
    for split_name, split_records in splits.items():
        write_jsonl(OUT / f"paper09_expanded_{split_name}.jsonl", split_records)
        write_jsonl(
            OUT / f"paper09_expanded_{split_name}_schema_only_sft.jsonl",
            [to_sft_record(r, include_temporal_metadata=False) for r in split_records],
        )
        write_jsonl(
            OUT / f"paper09_expanded_{split_name}_with_temporal_metadata_sft.jsonl",
            [to_sft_record(r, include_temporal_metadata=True) for r in split_records],
        )
        write_jsonl(OUT / f"paper09_expanded_{split_name}_ranking_pairs.jsonl", ranking_pairs[split_name])

    split_summary = {
        "seed": args.seed,
        "split_policy": "grouped_by_dataset_id_stratified_by_domain_and_year_max_bucket",
        "source_metadata": str(META_PATH),
        "data_root": str(DATA_ROOT),
        "splits": {name: summarize(split_records) for name, split_records in splits.items()},
        "ranking_pairs": {name: len(rows) for name, rows in ranking_pairs.items()},
    }
    (OUT / "expanded_split_summary.json").write_text(
        json.dumps(split_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_summary(
        OUT / "EXPANDED_CORPUS_SUMMARY.md",
        records=records,
        inventory=inventory,
        splits=splits,
        ranking_pairs=ranking_pairs,
    )

    print(f"Inventoried datasets: {len(inventory)}")
    print(f"Usable datasets: {len({r['dataset_id'] for r in records})}")
    print(f"Intent records: {len(records)}")
    print(f"Ranking pairs: {sum(len(v) for v in ranking_pairs.values())}")
    for split_name, split_records in splits.items():
        print(f"{split_name}: {len(split_records)} records / {len({r['dataset_id'] for r in split_records})} datasets")


if __name__ == "__main__":
    main()
