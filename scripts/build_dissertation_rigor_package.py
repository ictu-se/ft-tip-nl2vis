#!/usr/bin/env python3
"""Build statistical, slice, figure, and reproducibility artifacts for Paper 09."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "dissertation_rigor_20260621"
FIG = ROOT / "figures"

METRICS = [
    ("core_intent_ok", "Core"),
    ("full_intent_ok", "Full"),
    ("answerability_ok", "Answer."),
    ("temporal_filter_ok", "Temp. filter"),
]

RUNS = {
    "dev_schema_only": ROOT / "runs/overnight_full_dev_20260619/schema_only_lora_full_dev/full_dev_outputs.jsonl",
    "dev_metadata": ROOT / "runs/overnight_full_dev_20260619/metadata_lora_full_dev/full_dev_outputs.jsonl",
    "dev_unsupported_x4": ROOT / "runs/overnight_full_dev_20260619/unsupported_x4_lora_full_dev/full_dev_outputs.jsonl",
    "dev_planner_gate": ROOT / "runs/gate_balanced_smoke/composed_metadata_planner_gate_outputs.jsonl",
    "dev_planner_gate_constraint": ROOT / "runs/gate_balanced_smoke/composed_metadata_planner_gate_temporal_constrained_outputs.jsonl",
    "dev_rank16_l16": ROOT / "runs/dissertation_strength_20260621/qwen25_15b_expanded_metadata_rank16_l16_full_dev/full_dev_outputs.jsonl",
    "dev_rank8_all_layers": ROOT / "runs/dissertation_strength_20260621/qwen25_15b_expanded_metadata_rank8_all_layers_full_dev/full_dev_outputs.jsonl",
    "test_planner": ROOT / "runs/final_test_20260620/planner_test_outputs.jsonl",
    "test_final_policy": ROOT / "runs/final_test_20260620/composed_planner_gate_temporal_constrained_test_outputs.jsonl",
    "audit_vi_diacritic": ROOT / "runs/optional_external_multilingual_20260621/planner_vi_diacritic_dev/outputs.jsonl",
    "audit_non_worldbank": ROOT / "runs/optional_external_multilingual_20260621/planner_non_worldbank_dev/outputs.jsonl",
}

RAW_SPLITS = {
    "dev": ROOT / "benchmark_expanded/paper09_expanded_dev.jsonl",
    "test": ROOT / "benchmark_expanded/paper09_expanded_test.jsonl",
}

REQUIRED_FILES = [
    ROOT / "draft/main.tex",
    ROOT / "training/checkpoint_selection_protocol.md",
    ROOT / "FINAL_TEST_COMMANDS.md",
    ROOT / "scripts/run_final_test_once.sh",
    ROOT / "scripts/run_mlx_intent_inference.py",
    ROOT / "scripts/run_mlx_gate_inference.py",
    ROOT / "scripts/run_mlx_ranker_inference.py",
    ROOT / "runs/final_test_20260620/FINAL_TEST_RESULT.md",
    ROOT / "runs/final_test_20260620/composed_planner_gate_temporal_constrained_test_summary.json",
    ROOT / "runs/final_test_20260620/ranker_test_summary.json",
    ROOT / "runs/final_test_20260620/ranker_test_swapped_summary.json",
    ROOT / "runs/final_test_20260620/symmetric_ranker_policy/symmetric_ranker_policy_summary.json",
    ROOT / "runs/optional_external_multilingual_20260621/planner_vi_diacritic_dev/summary.json",
    ROOT / "runs/optional_external_multilingual_20260621/planner_non_worldbank_dev/summary.json",
    ROOT / "runs/optional_external_multilingual_20260621/prompt_mistral_7b_dev64/dev64_summary.json",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def pct(value: float, total: float) -> float:
    return 100.0 * value / total if total else 0.0


def mean_bool(rows: list[dict[str, Any]], metric: str) -> float:
    return pct(sum(bool(r.get(metric)) for r in rows), len(rows))


def bootstrap_ci(rows: list[dict[str, Any]], metric: str, *, seed: int, reps: int = 2000) -> tuple[float, float]:
    values = [1.0 if row.get(metric) else 0.0 for row in rows]
    n = len(values)
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(reps):
        total = 0.0
        for _ in range(n):
            total += values[rng.randrange(n)]
        samples.append(100.0 * total / n)
    samples.sort()
    return samples[int(0.025 * reps)], samples[int(0.975 * reps)]


def paired_mcnemar(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    by_a = {str(r.get("sample_id")): r for r in rows_a}
    by_b = {str(r.get("sample_id")): r for r in rows_b}
    ids = sorted(set(by_a) & set(by_b))
    both = a_only = b_only = neither = 0
    for sample_id in ids:
        a = bool(by_a[sample_id].get(metric))
        b = bool(by_b[sample_id].get(metric))
        if a and b:
            both += 1
        elif a:
            a_only += 1
        elif b:
            b_only += 1
        else:
            neither += 1
    discordant = a_only + b_only
    if discordant == 0:
        p_value = 1.0
    else:
        z = max(0.0, abs(a_only - b_only) - 1.0) / math.sqrt(discordant)
        p_value = math.erfc(z / math.sqrt(2.0))
    return {
        "n": len(ids),
        "both_correct": both,
        "a_only": a_only,
        "b_only": b_only,
        "neither": neither,
        "a_pct": round(pct(both + a_only, len(ids)), 4),
        "b_pct": round(pct(both + b_only, len(ids)), 4),
        "delta_b_minus_a": round(pct(b_only - a_only, len(ids)), 4),
        "mcnemar_p_approx": round(p_value, 8),
    }


def temporal_bucket(meta: dict[str, Any]) -> str:
    year_max = meta.get("year_max")
    distinct = int(meta.get("distinct_years") or 0)
    if year_max is not None and year_max <= 2010:
        recency = "old_end_<=2010"
    elif year_max is not None and year_max >= 2023:
        recency = "recent_end_>=2023"
    else:
        recency = "mid_end_2011_2022"
    if distinct <= 10:
        coverage = "short"
    elif distinct <= 25:
        coverage = "medium"
    elif distinct <= 50:
        coverage = "long"
    else:
        coverage = "very_long"
    return f"{recency}/{coverage}"


def source_family(source: str) -> str:
    text = source.lower()
    if "world bank" in text and "owid" not in text:
        return "world_bank"
    if "owid" in text or "our world in data" in text:
        return "owid_or_derived"
    return "other"


def enrich(rows: list[dict[str, Any]], raw: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        record = raw.get(str(row.get("sample_id")), {})
        meta = record.get("temporal_metadata") or {}
        gold = row.get("gold") or record.get("gold_intent") or {}
        pred = row.get("prediction") or {}
        item = dict(row)
        item["domain"] = record.get("domain", "")
        item["source"] = record.get("source", "")
        item["source_family"] = source_family(str(record.get("source", "")))
        item["temporal_bucket"] = temporal_bucket(meta)
        item["answerability"] = gold.get("answerability", record.get("answerability", ""))
        item["gold_task_type"] = gold.get("task_type", row.get("task_type", ""))
        item["pred_task_type"] = pred.get("task_type", "") if isinstance(pred, dict) else ""
        item["gold_temporal_filter"] = gold.get("temporal_filter", "")
        item["pred_temporal_filter"] = pred.get("temporal_filter", "") if isinstance(pred, dict) else ""
        out.append(item)
    return out


def slice_rows(rows: list[dict[str, Any]], keys: Iterable[str], min_n: int = 20) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key in keys:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(key, ""))].append(row)
        for value, group in sorted(groups.items()):
            if len(group) < min_n:
                continue
            result.append(
                {
                    "slice": key,
                    "value": value,
                    "n": len(group),
                    "core_pct": round(mean_bool(group, "core_intent_ok"), 4),
                    "full_pct": round(mean_bool(group, "full_intent_ok"), 4),
                    "answerability_pct": round(mean_bool(group, "answerability_ok"), 4),
                    "temporal_filter_pct": round(mean_bool(group, "temporal_filter_ok"), 4),
                    "false_plot_pct": round(
                        pct(
                            sum(
                                (r.get("gold") or {}).get("answerability") == "unanswerable"
                                and (r.get("prediction") or {}).get("answerability") == "answerable"
                                for r in group
                            ),
                            len(group),
                        ),
                        4,
                    ),
                }
            )
    return result


def task_confusion(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter()
    for row in rows:
        if row.get("task_type_ok"):
            continue
        counts[(row.get("gold_task_type", ""), row.get("pred_task_type", ""))] += 1
    total = len(rows)
    return [
        {
            "gold_task_type": gold,
            "pred_task_type": pred,
            "count": count,
            "rate_pct": round(pct(count, total), 4),
        }
        for (gold, pred), count in counts.most_common()
    ]


def build_ci_table(loaded: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    selected = {
        "Dev schema-only": "dev_schema_only",
        "Dev metadata": "dev_metadata",
        "Dev final policy": "dev_planner_gate_constraint",
        "Test planner": "test_planner",
        "Test final policy": "test_final_policy",
        "VI diacritic audit": "audit_vi_diacritic",
        "Non-WB audit": "audit_non_worldbank",
    }
    rows: list[dict[str, Any]] = []
    seed = 20260621
    for label, run_key in selected.items():
        data = loaded[run_key]
        for idx, (metric, metric_label) in enumerate(METRICS):
            lo, hi = bootstrap_ci(data, metric, seed=seed + idx + 17 * len(rows))
            rows.append(
                {
                    "run": label,
                    "metric": metric_label,
                    "n": len(data),
                    "estimate_pct": round(mean_bool(data, metric), 4),
                    "ci95_low_pct": round(lo, 4),
                    "ci95_high_pct": round(hi, 4),
                }
            )
    return rows


def build_paired_tests(loaded: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    comparisons = [
        ("Dev schema-only", "Dev metadata", "dev_schema_only", "dev_metadata"),
        ("Dev metadata", "Dev unsupported-x4", "dev_metadata", "dev_unsupported_x4"),
        ("Dev metadata", "Dev final policy", "dev_metadata", "dev_planner_gate_constraint"),
        ("Dev rank16 last16", "Dev rank8 all-layer", "dev_rank16_l16", "dev_rank8_all_layers"),
        ("Test planner", "Test final policy", "test_planner", "test_final_policy"),
    ]
    rows: list[dict[str, Any]] = []
    for a_label, b_label, a_key, b_key in comparisons:
        for metric, metric_label in METRICS:
            item = paired_mcnemar(loaded[a_key], loaded[b_key], metric)
            item.update({"a": a_label, "b": b_label, "metric": metric_label})
            rows.append(item)
    return rows


def write_latex_tables(ci_rows: list[dict[str, Any]], paired_rows: list[dict[str, Any]]) -> None:
    selected_ci = [
        r
        for r in ci_rows
        if r["run"] in {"Test planner", "Test final policy", "VI diacritic audit", "Non-WB audit"}
        and r["metric"] in {"Core", "Full", "Answer.", "Temp. filter"}
    ]
    lines = [
        "% Auto-generated by scripts/build_dissertation_rigor_package.py",
        "\\begin{tabular}{llrrr}",
        "\\toprule",
        "Run & Metric & Estimate & 95\\% CI low & 95\\% CI high\\\\",
        "\\midrule",
    ]
    for r in selected_ci:
        lines.append(
            f"{r['run']} & {r['metric']} & {r['estimate_pct']:.2f} & "
            f"{r['ci95_low_pct']:.2f} & {r['ci95_high_pct']:.2f}\\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    (OUT / "statistical_ci_table.tex").write_text("\n".join(lines), encoding="utf-8")

    selected_pairs = [
        r
        for r in paired_rows
        if (r["a"], r["b"], r["metric"])
        in {
            ("Dev schema-only", "Dev metadata", "Full"),
            ("Dev metadata", "Dev final policy", "Full"),
            ("Dev metadata", "Dev final policy", "Answer."),
            ("Test planner", "Test final policy", "Full"),
            ("Test planner", "Test final policy", "Answer."),
            ("Dev rank16 last16", "Dev rank8 all-layer", "Temp. filter"),
        }
    ]
    lines = [
        "% Auto-generated by scripts/build_dissertation_rigor_package.py",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Comparison & Metric & A & B & $\\Delta$ & $p$\\\\",
        "\\midrule",
    ]
    for r in selected_pairs:
        comp = f"{r['a']} $\\rightarrow$ {r['b']}"
        p = "<0.0001" if r["mcnemar_p_approx"] < 0.0001 else f"{r['mcnemar_p_approx']:.4f}"
        lines.append(
            f"{comp} & {r['metric']} & {r['a_pct']:.2f} & {r['b_pct']:.2f} & "
            f"{r['delta_b_minus_a']:.2f} & {p}\\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    (OUT / "paired_tests_table.tex").write_text("\n".join(lines), encoding="utf-8")


def make_figures(ci_rows: list[dict[str, Any]], failure_csv: Path) -> None:
    import matplotlib.pyplot as plt

    FIG.mkdir(parents=True, exist_ok=True)

    # Figure 1 is maintained as Mermaid source in figures/ft_tip_architecture.mmd
    # and rendered with mermaid-cli so the architecture diagram remains editable.

    final_ci = [
        r
        for r in ci_rows
        if r["run"] == "Test final policy" and r["metric"] in {"Core", "Full", "Answer.", "Temp. filter"}
    ]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    xs = list(range(len(final_ci)))
    ys = [r["estimate_pct"] for r in final_ci]
    yerr = [
        [r["estimate_pct"] - r["ci95_low_pct"] for r in final_ci],
        [r["ci95_high_pct"] - r["estimate_pct"] for r in final_ci],
    ]
    ax.bar(xs, ys, color=["#2f6f9f", "#4f8f6f", "#b7791f", "#805ad5"])
    ax.errorbar(xs, ys, yerr=yerr, fmt="none", ecolor="#222222", capsize=4, lw=1)
    ax.set_xticks(xs, [r["metric"] for r in final_ci])
    ax.set_ylim(80, 101)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Frozen test policy accuracy with bootstrap 95% CIs")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "final_test_ci.pdf")
    plt.close(fig)

    failures = []
    with failure_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            failures.append(row)
    top = failures[:6]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    labels = [r["Failure type"] if "Failure type" in r else r.get("failure_type", "") for r in top]
    vals = [float(r["Rate"] if "Rate" in r else r.get("rate_pct", 0.0)) for r in top]
    labels = [label.replace("_", " ") for label in labels]
    ax.barh(list(range(len(vals))), vals, color="#9f3a38")
    ax.set_yticks(list(range(len(vals))), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Rate over test records (%)")
    ax.set_title("Frozen test residual failure decomposition")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "final_failure_decomposition.pdf")
    plt.close(fig)


def write_reproducibility(check_rows: list[dict[str, Any]]) -> None:
    missing = [r for r in check_rows if not r["exists"]]
    lines = [
        "# Paper 09 Reproducibility Checklist",
        "",
        "Generated by `scripts/build_dissertation_rigor_package.py`.",
        "",
        "## Frozen-Test Rule",
        "",
        "The expanded test split was evaluated once after the method, adapters, scripts, and decision rules were frozen. Do not tune the method from the final-test result.",
        "",
        "## Key Commands",
        "",
        "- Final test: `bash scripts/run_final_test_once.sh`",
        "- Optional audits: `bash scripts/run_optional_external_multilingual_audits.sh`",
        "- Dissertation-rigor package: `python3 scripts/build_dissertation_rigor_package.py`",
        "- Compile manuscript: `cd draft && latexmk -pdf -interaction=nonstopmode main.tex`",
        "",
        "## Required Artifacts",
        "",
        "| Artifact | Exists |",
        "| --- | ---: |",
    ]
    for row in check_rows:
        lines.append(f"| `{row['path']}` | {'yes' if row['exists'] else 'no'} |")
    lines += [
        "",
        "## Generated Rigor Artifacts",
        "",
        "- `runs/dissertation_rigor_20260621/bootstrap_metric_ci.csv`",
        "- `runs/dissertation_rigor_20260621/paired_mcnemar_tests.csv`",
        "- `runs/dissertation_rigor_20260621/final_test_slice_matrix.csv`",
        "- `runs/dissertation_rigor_20260621/final_test_task_confusions.csv`",
        "- `figures/ft_tip_architecture.pdf`",
        "- `figures/final_test_ci.pdf`",
        "- `figures/final_failure_decomposition.pdf`",
    ]
    if missing:
        lines += ["", "## Missing", ""]
        for row in missing:
            lines.append(f"- `{row['path']}`")
    (ROOT / "REPRODUCIBILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    loaded = {key: read_jsonl(path) for key, path in RUNS.items()}
    raw_dev = {r["sample_id"]: r for r in read_jsonl(RAW_SPLITS["dev"])}
    raw_test = {r["sample_id"]: r for r in read_jsonl(RAW_SPLITS["test"])}

    ci_rows = build_ci_table(loaded)
    paired_rows = build_paired_tests(loaded)
    final_enriched = enrich(loaded["test_final_policy"], raw_test)
    vi_enriched = enrich(loaded["audit_vi_diacritic"], raw_dev)
    nonwb_enriched = enrich(loaded["audit_non_worldbank"], raw_dev)

    final_slices = slice_rows(
        final_enriched,
        ["language", "domain", "source_family", "task_type", "answerability", "temporal_bucket"],
        min_n=20,
    )
    audit_slices = []
    for audit_name, rows in [("vi_diacritic", vi_enriched), ("non_worldbank", nonwb_enriched)]:
        for row in slice_rows(rows, ["language", "domain", "task_type", "answerability"], min_n=5):
            row["audit"] = audit_name
            audit_slices.append(row)

    confusions = task_confusion(final_enriched)
    check_rows = [
        {"path": str(path.relative_to(ROOT)), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0}
        for path in REQUIRED_FILES
    ]

    write_csv(OUT / "bootstrap_metric_ci.csv", ci_rows)
    write_csv(OUT / "paired_mcnemar_tests.csv", paired_rows)
    write_csv(OUT / "final_test_slice_matrix.csv", final_slices)
    write_csv(OUT / "optional_audit_slice_matrix.csv", audit_slices)
    write_csv(OUT / "final_test_task_confusions.csv", confusions)
    write_csv(OUT / "reproducibility_file_check.csv", check_rows)
    write_latex_tables(ci_rows, paired_rows)
    make_figures(ci_rows, ROOT / "runs/final_test_20260620/failure_analysis/policy_failure_taxonomy.csv")
    write_reproducibility(check_rows)

    summary = {
        "ci_rows": len(ci_rows),
        "paired_tests": len(paired_rows),
        "final_slice_rows": len(final_slices),
        "optional_audit_slice_rows": len(audit_slices),
        "task_confusion_rows": len(confusions),
        "missing_reproducibility_files": [r["path"] for r in check_rows if not r["exists"]],
    }
    (OUT / "rigor_package_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
