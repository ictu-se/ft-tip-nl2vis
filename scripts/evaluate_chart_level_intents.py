#!/usr/bin/env python3
"""Evaluate intent-to-Vega-Lite chart readiness for Paper 09 outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

try:
    import vl_convert as vlc
except Exception:  # pragma: no cover - optional local dependency
    vlc = None


CHART_KEYS = [
    "answerability",
    "chart_type",
    "time_field",
    "measure",
    "secondary_measure",
    "group_by",
    "temporal_filter",
    "temporal_granularity",
    "statistic",
    "aggregation",
    "sort",
    "top_k",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pct(num: int | float, den: int | float) -> float:
    return round(100.0 * num / den, 4) if den else 0.0


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def normalize_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def load_csv_values(path: Path, limit: int = 500) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    values = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append({k: coerce_scalar(v) for k, v in row.items()})
            if len(values) >= limit:
                break
    return values


def coerce_scalar(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        if re.fullmatch(r"-?\d+", text):
            return int(text)
        if re.fullmatch(r"-?(\d+\.\d*|\d*\.\d+)([eE]-?\d+)?", text):
            return float(text)
    except Exception:
        return text
    return text


def schema_field_types(record: dict[str, Any]) -> dict[str, str]:
    out = {}
    for item in record.get("schema") or []:
        name = item.get("name")
        if name:
            out[str(name)] = str(item.get("type") or "")
    return out


def schema_fields(record: dict[str, Any]) -> set[str]:
    return set(schema_field_types(record))


def parse_year_range(filter_name: str, meta: dict[str, Any]) -> tuple[int | None, int | None]:
    text = normalize_empty(filter_name)
    if text in {"", "all_years", "none"}:
        return None, None
    if text == "latest_year":
        latest = meta.get("latest_year") or meta.get("year_max")
        return int(latest), int(latest)
    if text in {"recent_10_years", "last_10_years"}:
        return int(meta["recent_10_start"]), int(meta["recent_10_end"])
    if text == "previous_10_years":
        return int(meta["previous_10_start"]), int(meta["previous_10_end"])
    if re.fullmatch(r"\d{4}", text):
        year = int(text)
        return year, year
    match = re.fullmatch(r"(\d{4})-(\d{4})", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.fullmatch(r"(\d{4})_to_(\d{4})", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def field_type(field: str, record: dict[str, Any]) -> str:
    ftype = schema_field_types(record).get(field, "")
    if ftype == "temporal":
        return "quantitative"
    if ftype == "nominal":
        return "nominal"
    if ftype == "ordinal":
        return "ordinal"
    return "quantitative"


def mark_for(chart_type: str) -> str:
    chart_type = normalize_empty(chart_type)
    return {
        "line": "line",
        "bar": "bar",
        "boxplot": "boxplot",
        "scatter": "point",
        "point": "point",
        "histogram": "bar",
    }.get(chart_type, "")


def valid_intent_fields(intent: dict[str, Any], record: dict[str, Any]) -> tuple[bool, list[str]]:
    fields = schema_fields(record)
    needed = []
    for key in ["time_field", "measure", "secondary_measure", "group_by"]:
        value = normalize_empty(intent.get(key))
        if value and value != "none":
            needed.append(value)
    for value in intent.get("required_fields") or []:
        value = normalize_empty(value)
        if value:
            needed.append(value)
    missing = sorted({field for field in needed if field not in fields})
    return not missing, missing


def intent_to_spec(
    intent: dict[str, Any],
    record: dict[str, Any],
    data_dir: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    info: dict[str, Any] = {"reason": "", "missing_fields": []}
    if not isinstance(intent, dict):
        info["reason"] = "non_dict_intent"
        return None, info
    if intent.get("answerability") != "answerable":
        info["reason"] = "unanswerable_intent"
        return None, info

    field_ok, missing = valid_intent_fields(intent, record)
    info["missing_fields"] = missing
    if not field_ok:
        info["reason"] = "missing_schema_fields"
        return None, info

    mark = mark_for(intent.get("chart_type", ""))
    if not mark:
        info["reason"] = "unsupported_chart_type"
        return None, info

    dataset_id = str(record.get("dataset_id") or "")
    values = load_csv_values(data_dir / f"{dataset_id}.csv")
    if not values:
        info["reason"] = "missing_or_empty_csv"
        return None, info

    time_field = normalize_empty(intent.get("time_field"))
    measure = normalize_empty(intent.get("measure"))
    group_by = normalize_empty(intent.get("group_by"))
    secondary = normalize_empty(intent.get("secondary_measure"))
    statistic = normalize_empty(intent.get("statistic"))
    aggregation = normalize_empty(intent.get("aggregation"))

    encoding: dict[str, Any] = {}
    if mark == "line":
        encoding["x"] = {"field": time_field, "type": field_type(time_field, record)}
        encoding["y"] = {"field": measure, "type": "quantitative"}
        if group_by and group_by != "none":
            encoding["color"] = {"field": group_by, "type": field_type(group_by, record)}
    elif mark == "point":
        x_field = secondary or time_field or group_by
        encoding["x"] = {"field": x_field, "type": field_type(x_field, record)}
        encoding["y"] = {"field": measure, "type": "quantitative"}
        if group_by and group_by != "none":
            encoding["color"] = {"field": group_by, "type": field_type(group_by, record)}
    elif mark == "boxplot":
        encoding["y"] = {"field": measure, "type": "quantitative"}
        if group_by and group_by != "none":
            encoding["x"] = {"field": group_by, "type": field_type(group_by, record)}
    else:
        x_field = group_by if group_by and group_by != "none" else time_field
        encoding["x"] = {"field": x_field, "type": field_type(x_field, record)}
        encoding["y"] = {"field": measure, "type": "quantitative"}
        if aggregation in {"mean", "sum", "median", "min", "max", "count"}:
            encoding["y"]["aggregate"] = aggregation
        elif statistic in {"mean", "average"}:
            encoding["y"]["aggregate"] = "mean"
        if intent.get("sort") == "desc":
            encoding["x"]["sort"] = "-y"
        elif intent.get("sort") == "asc":
            encoding["x"]["sort"] = "y"

    transforms = []
    meta = record.get("temporal_metadata") or {}
    start, end = parse_year_range(normalize_empty(intent.get("temporal_filter")), meta)
    if time_field and start is not None and end is not None:
        if start == end:
            transforms.append({"filter": f"datum['{time_field}'] == {start}"})
        else:
            transforms.append(
                {"filter": f"datum['{time_field}'] >= {start} && datum['{time_field}'] <= {end}"}
            )

    top_k = intent.get("top_k")
    if isinstance(top_k, int) and top_k > 0 and group_by and group_by != "none":
        transforms.extend(
            [
                {
                    "window": [{"op": "rank", "as": "rank"}],
                    "sort": [{"field": measure, "order": "descending"}],
                },
                {"filter": f"datum.rank <= {top_k}"},
            ]
        )

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": f"Paper09 audit spec for {record.get('sample_id')}",
        "data": {"values": values},
        "mark": mark,
        "encoding": encoding,
    }
    if transforms:
        spec["transform"] = transforms
    return spec, info


def spec_signature(spec: dict[str, Any] | None) -> dict[str, Any]:
    if not spec:
        return {}
    enc = spec.get("encoding") or {}
    transforms = spec.get("transform") or []
    return {
        "mark": spec.get("mark"),
        "x": (enc.get("x") or {}).get("field", ""),
        "y": (enc.get("y") or {}).get("field", ""),
        "color": (enc.get("color") or {}).get("field", ""),
        "x_sort": (enc.get("x") or {}).get("sort", ""),
        "y_aggregate": (enc.get("y") or {}).get("aggregate", ""),
        "filters": tuple(t.get("filter", "") for t in transforms if "filter" in t),
        "has_topk": any("window" in t for t in transforms),
    }


def render_svg_ok(spec: dict[str, Any] | None) -> tuple[bool, str]:
    if spec is None:
        return False, "no_spec"
    if vlc is None:
        return False, "vl_convert_unavailable"
    try:
        svg = vlc.vegalite_to_svg(spec)
        if isinstance(svg, str) and "<svg" in svg:
            return True, ""
        return False, "empty_svg"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:180]}"


def stratified_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        gold = row.get("gold") or {}
        key = (
            str(row.get("task_type", "")),
            str(row.get("language", "")),
            str(gold.get("answerability", "")),
            bool(row.get("full_intent_ok")),
        )
        groups[key].append(row)
    for group in groups.values():
        group.sort(key=lambda item: str(item.get("sample_id", "")))

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


def classify_chart_error(row: dict[str, Any]) -> str:
    if row["gold_answerability"] == "unanswerable" and row["pred_answerability"] == "answerable":
        return "false_plot"
    if row["gold_answerability"] == "answerable" and row["pred_answerability"] == "unanswerable":
        return "over_refusal"
    if row["gold_answerability"] == "unanswerable" and row["pred_answerability"] == "unanswerable":
        return "safe_refusal"
    if not row["pred_spec_constructed"]:
        return row["pred_spec_reason"] or "no_spec"
    if not row["render_valid"]:
        return "render_failure"
    if row["chart_semantic_ok"]:
        return "semantic_ok"
    pred_sig = row.get("pred_signature") or {}
    gold_sig = row.get("gold_signature") or {}
    for key, label in [
        ("mark", "wrong_mark"),
        ("x", "wrong_x_field"),
        ("y", "wrong_y_field"),
        ("color", "wrong_grouping"),
        ("filters", "wrong_filter"),
        ("has_topk", "wrong_topk"),
    ]:
        if pred_sig.get(key) != gold_sig.get(key):
            return label
    return "other_semantic_mismatch"


def evaluate(args: argparse.Namespace) -> None:
    predictions = read_jsonl(args.predictions)
    records = read_jsonl(args.records)
    records_by_id = {str(row["sample_id"]): row for row in records}
    joined = [row for row in predictions if str(row.get("sample_id")) in records_by_id]
    sample = stratified_sample(joined, args.limit)

    out_rows = []
    for row in sample:
        record = records_by_id[str(row["sample_id"])]
        pred = row.get("prediction") or {}
        gold = row.get("gold") or {}
        pred_spec, pred_info = intent_to_spec(pred, record, args.data_dir)
        gold_spec, gold_info = intent_to_spec(gold, record, args.data_dir)
        pred_render_ok, pred_render_error = render_svg_ok(pred_spec)
        gold_render_ok, gold_render_error = render_svg_ok(gold_spec)
        pred_sig = spec_signature(pred_spec)
        gold_sig = spec_signature(gold_spec)
        chart_semantic_ok = (
            normalize_empty(pred.get("answerability")) == normalize_empty(gold.get("answerability"))
            and (
                normalize_empty(gold.get("answerability")) == "unanswerable"
                or (pred_sig == gold_sig and pred_render_ok and gold_render_ok)
            )
        )
        item = {
            "sample_id": row.get("sample_id"),
            "dataset_id": row.get("dataset_id"),
            "language": row.get("language"),
            "task_type": row.get("task_type"),
            "query": record.get("query", ""),
            "gold_answerability": gold.get("answerability", ""),
            "pred_answerability": pred.get("answerability", ""),
            "full_intent_ok": bool(row.get("full_intent_ok")),
            "core_intent_ok": bool(row.get("core_intent_ok")),
            "pred_spec_constructed": pred_spec is not None,
            "gold_spec_constructed": gold_spec is not None,
            "render_valid": pred_render_ok,
            "gold_render_valid": gold_render_ok,
            "render_error": pred_render_error,
            "gold_render_error": gold_render_error,
            "chart_semantic_ok": chart_semantic_ok,
            "pred_spec_reason": pred_info.get("reason", ""),
            "gold_spec_reason": gold_info.get("reason", ""),
            "pred_missing_fields": pred_info.get("missing_fields", []),
            "gold_missing_fields": gold_info.get("missing_fields", []),
            "pred_signature": pred_sig,
            "gold_signature": gold_sig,
            "pred_intent": pred,
            "gold_intent": gold,
        }
        item["chart_error_type"] = classify_chart_error(item)
        out_rows.append(item)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs_path = args.output_dir / "chart_level_outputs.jsonl"
    with outputs_path.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    n = len(out_rows)
    predicted_answerable = [r for r in out_rows if r["pred_answerability"] == "answerable"]
    constructed = [r for r in out_rows if r["pred_spec_constructed"]]
    gold_answerable = [r for r in out_rows if r["gold_answerability"] == "answerable"]
    summary = {
        "sample_n": n,
        "joined_population_n": len(joined),
        "renderer": "vl-convert" if vlc is not None else "unavailable",
        "predicted_answerable_n": len(predicted_answerable),
        "gold_answerable_n": len(gold_answerable),
        "pred_spec_constructed_pct_all": pct(sum(r["pred_spec_constructed"] for r in out_rows), n),
        "pred_spec_constructed_pct_pred_answerable": pct(
            sum(r["pred_spec_constructed"] for r in predicted_answerable), len(predicted_answerable)
        ),
        "render_valid_pct_all": pct(sum(r["render_valid"] for r in out_rows), n),
        "render_valid_pct_constructed": pct(sum(r["render_valid"] for r in constructed), len(constructed)),
        "chart_semantic_accuracy_pct_all": pct(sum(r["chart_semantic_ok"] for r in out_rows), n),
        "chart_semantic_accuracy_pct_gold_answerable": pct(
            sum(r["chart_semantic_ok"] for r in gold_answerable), len(gold_answerable)
        ),
        "false_plot_rate_pct": pct(
            sum(r["gold_answerability"] == "unanswerable" and r["pred_answerability"] == "answerable" for r in out_rows),
            n,
        ),
        "over_refusal_rate_pct": pct(
            sum(r["gold_answerability"] == "answerable" and r["pred_answerability"] == "unanswerable" for r in out_rows),
            n,
        ),
        "error_type_counts": Counter(r["chart_error_type"] for r in out_rows),
    }
    summary["error_type_counts"] = dict(summary["error_type_counts"])
    (args.output_dir / "chart_level_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    write_summary_table(args.output_dir / "chart_level_table.tex", summary)
    write_error_table(args.output_dir / "chart_level_error_table.tex", out_rows)
    write_case_table(args.output_dir / "chart_level_cases.tex", out_rows)
    write_outcome_figure(args.output_dir / "chart_level_outcomes.pdf", out_rows)


def write_summary_table(path: Path, summary: dict[str, Any]) -> None:
    rows = [
        ("Sampled frozen-test intents", summary["sample_n"], "--"),
        ("Predicted answerable", summary["predicted_answerable_n"], "--"),
        ("Spec constructed / predicted answerable", "--", summary["pred_spec_constructed_pct_pred_answerable"]),
        ("Rendered SVG / constructed specs", "--", summary["render_valid_pct_constructed"]),
        ("Chart-semantic accuracy / all sampled", "--", summary["chart_semantic_accuracy_pct_all"]),
        ("Chart-semantic accuracy / gold answerable", "--", summary["chart_semantic_accuracy_pct_gold_answerable"]),
        ("False-plot rate / all sampled", "--", summary["false_plot_rate_pct"]),
        ("Over-refusal rate / all sampled", "--", summary["over_refusal_rate_pct"]),
    ]
    lines = [
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Audit statistic & Count & Percent \\",
        r"\midrule",
    ]
    for label, count, percent in rows:
        pct_text = "--" if percent == "--" else f"{float(percent):.2f}"
        lines.append(f"{latex_escape(label)} & {count} & {pct_text} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_error_table(path: Path, rows: list[dict[str, Any]]) -> None:
    counter = Counter(row["chart_error_type"] for row in rows)
    total = len(rows)
    lines = [
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Chart-level outcome & Count & Percent \\",
        r"\midrule",
    ]
    for key, count in counter.most_common():
        lines.append(f"{latex_escape(key)} & {count} & {pct(count, total):.2f} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outcome_figure(path: Path, rows: list[dict[str, Any]]) -> None:
    counter = Counter(row["chart_error_type"] for row in rows)
    order = [
        "semantic_ok",
        "safe_refusal",
        "wrong_mark",
        "false_plot",
        "missing_schema_fields",
        "wrong_y_field",
        "wrong_x_field",
        "over_refusal",
        "render_failure",
    ]
    labels = [key for key in order if counter.get(key)]
    values = [counter[key] for key in labels]
    pretty = [label.replace("_", " ") for label in labels]
    colors = []
    for label in labels:
        if label in {"semantic_ok", "safe_refusal"}:
            colors.append("#2d6a4f")
        elif label in {"false_plot", "over_refusal"}:
            colors.append("#b23a48")
        else:
            colors.append("#457b9d")
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    bars = ax.barh(pretty, values, color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Count in stratified 200-sample chart audit")
    ax.set_title("Chart-level outcomes after intent-to-Vega-Lite conversion")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, value in zip(bars, values):
        ax.text(value + 1, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=9)
    ax.set_xlim(0, max(values) * 1.18)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def intent_short(intent: dict[str, Any]) -> str:
    if intent.get("answerability") == "unanswerable":
        return f"unanswerable/{intent.get('unsupported_reason', '') or intent.get('task_type', '')}"
    parts = [
        intent.get("chart_type", ""),
        intent.get("task_type", ""),
        intent.get("measure", ""),
        intent.get("temporal_filter", ""),
    ]
    group = intent.get("group_by")
    if group:
        parts.append(f"group={group}")
    return "/".join(str(p) for p in parts if p)


def write_case_table(path: Path, rows: list[dict[str, Any]]) -> None:
    wanted = [
        "semantic_ok",
        "safe_refusal",
        "wrong_mark",
        "wrong_grouping",
        "false_plot",
        "missing_schema_fields",
        "wrong_y_field",
        "wrong_x_field",
        "wrong_topk",
    ]
    selected = []
    seen = set()
    for kind in wanted:
        for row in rows:
            if kind == "semantic_ok" and not row.get("full_intent_ok"):
                continue
            if row["chart_error_type"] == kind and row["sample_id"] not in seen:
                selected.append(row)
                seen.add(row["sample_id"])
                break
    for row in rows:
        if len(selected) >= 6:
            break
        if row["sample_id"] not in seen:
            selected.append(row)
            seen.add(row["sample_id"])

    lines = [
        r"\begin{tabular}{p{0.23\linewidth}p{0.20\linewidth}p{0.20\linewidth}p{0.23\linewidth}}",
        r"\toprule",
        r"Query & Gold chart intent & Predicted chart intent & Chart-level reading \\",
        r"\midrule",
    ]
    for row in selected[:6]:
        reading = row["chart_error_type"]
        if reading == "semantic_ok":
            reading = "Renderable and semantically aligned with the gold intent."
        elif reading == "safe_refusal":
            reading = "No chart is produced; the unsupported request is refused safely."
        elif reading == "false_plot":
            reading = "A renderable chart is produced for an unsupported request; this is the most serious residual safety error."
        elif reading == "wrong_filter":
            reading = "The chart renders, but the temporal filter changes the analytical answer."
        elif reading == "wrong_mark":
            reading = "The chart renders, but the chosen mark encodes a different analytical operation."
        elif reading == "missing_schema_fields":
            reading = "Spec generation is blocked because the predicted required fields include a non-schema field."
        elif reading == "wrong_y_field":
            reading = "The chart renders, but the predicted measure changes the analytical quantity."
        elif reading == "wrong_x_field":
            reading = "The chart renders, but the predicted x field changes the analytical relation."
        elif reading == "wrong_topk":
            reading = "The chart renders, but the ranking constraint is not semantically aligned."
        lines.append(
            "{} & {} & {} & {} \\\\".format(
                latex_escape(row["query"][:180]),
                latex_escape(intent_short(row["gold_intent"])),
                latex_escape(intent_short(row["pred_intent"])),
                latex_escape(reading),
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=200)
    return parser.parse_args()


if __name__ == "__main__":
    evaluate(parse_args())
