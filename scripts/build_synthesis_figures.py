#!/usr/bin/env python3
"""Build synthesis figures for Paper 09 from completed experiment results."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)


def architecture_cascade() -> None:
    labels = [
        "Prompt\nonly",
        "Schema\nplanner",
        "Metadata\nplanner",
        "Unsupported\nx4",
        "Planner\n+ gate",
        "Gate +\nconstraint",
    ]
    full = [0.00, 72.62, 84.22, 79.23, 87.95, 88.01]
    answer = [0.00, 85.19, 85.19, 86.85, 99.17, 99.17]
    temp = [0.00, 82.10, 93.09, 85.81, 93.09, 93.15]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.2, 3.3))
    ax.plot(x, full, marker="o", linewidth=2.2, label="Full intent")
    ax.plot(x, answer, marker="s", linewidth=2.0, label="Answerability")
    ax.plot(x, temp, marker="^", linewidth=2.0, label="Temporal filter")
    ax.set_ylim(-2, 105)
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Architecture evidence is a sequence of distinct gains")
    ax.grid(axis="y", alpha=0.22)
    ax.legend(loc="lower right", ncol=3, frameon=False)
    ax.annotate(
        "+ temporal\nsupport",
        xy=(2, full[2]),
        xytext=(1.35, 96),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
        ha="center",
    )
    ax.annotate(
        "gate fixes\nanswerability",
        xy=(4, answer[4]),
        xytext=(4.35, 73),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
        ha="center",
    )
    save(fig, "architecture_cascade.pdf")


def safety_frontier() -> None:
    labels = ["Metadata\nplanner", "Unsupported\nx4", "Planner\n+ gate"]
    false_plot = [14.81, 0.24, 0.83]
    over_refuse = [0.00, 12.91, 0.00]
    full = [84.22, 79.23, 87.95]
    colors = ["#8b8b8b", "#cc7a00", "#0072b2"]

    fig, ax = plt.subplots(figsize=(5.7, 4.0))
    sizes = [90 + 3 * v for v in full]
    for x, y, s, c, lab in zip(false_plot, over_refuse, sizes, colors, labels):
        ax.scatter(x, y, s=s, color=c, alpha=0.86, edgecolor="white", linewidth=1.1)
        ax.text(x + 0.35, y + 0.35, lab, va="bottom", fontsize=8)
    ax.set_xlim(-0.8, 16.5)
    ax.set_ylim(-0.8, 14.8)
    ax.set_xlabel("False plotting over full dev (%)")
    ax.set_ylabel("Over-refusal over full dev (%)")
    ax.set_title("Answerability gate dominates the safety frontier")
    ax.grid(alpha=0.2)
    ax.annotate(
        "unsafe plotting",
        xy=(14.81, 0),
        xytext=(8.5, 3.2),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )
    ax.annotate(
        "safe but too cautious",
        xy=(0.24, 12.91),
        xytext=(2.4, 11.0),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )
    ax.annotate(
        "preferred frontier",
        xy=(0.83, 0),
        xytext=(3.5, 1.8),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )
    save(fig, "safety_frontier.pdf")


def adapter_landscape() -> None:
    labels = [
        "r4\nL16",
        "r8\nL16",
        "r16\nL16",
        "r32\nL16",
        "r8\nL8",
        "r8\nall",
        "r16 L16\nfull-dev",
        "r8 all\nfull-dev",
    ]
    full = [85.94, 85.94, 95.31, 93.75, 76.56, 96.88, 95.63, 95.50]
    temp = [92.19, 96.88, 96.88, 96.88, 92.19, 100.00, 97.89, 99.88]
    answer = [87.50, 87.50, 96.88, 93.75, 87.50, 100.00, 97.71, 99.63]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    width = 0.25
    ax.bar(x - width, full, width, label="Full")
    ax.bar(x, temp, width, label="Temporal")
    ax.bar(x + width, answer, width, label="Answer.")
    ax.set_ylim(70, 102)
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Adapter capacity changes what the model learns")
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=3, loc="lower right")
    ax.axvline(5.5, color="black", linewidth=0.8, alpha=0.25)
    ax.text(2.5, 71.2, "dev64 screen", ha="center", va="bottom", fontsize=8)
    ax.text(6.5, 71.2, "full-dev confirmation", ha="center", va="bottom", fontsize=8)
    save(fig, "adapter_landscape.pdf")


def robustness_generalization() -> None:
    labels = ["Frozen\ntest", "Vietnamese\ndiacritic", "Non-WB\nschema"]
    core = [88.49, 81.68, 82.14]
    full = [88.30, 72.60, 76.79]
    temp = [93.73, 99.47, 94.64]
    answer = [99.10, 81.83, 85.71]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.8, 3.7))
    width = 0.2
    for offset, vals, lab in [
        (-1.5 * width, core, "Core"),
        (-0.5 * width, full, "Full"),
        (0.5 * width, temp, "Temporal"),
        (1.5 * width, answer, "Answer."),
    ]:
        ax.bar(x + offset, vals, width, label=lab)
    ax.set_ylim(65, 102)
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Robustness audits separate temporal grounding from full intent")
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=4, loc="lower center")
    save(fig, "robustness_generalization.pdf")


def ranker_sensitivity() -> None:
    path = ROOT / "runs/final_test_20260620/failure_analysis/ranker_task_sensitivity.csv"
    rows = []
    with path.open() as f:
        for row in csv.DictReader(f):
            rows.append((row["task_type"], float(row["fallback_pct"])))
    rows.sort(key=lambda x: x[1])
    labels = [r[0].replace("_", "\n") for r in rows]
    vals = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    colors = ["#0072b2" if v < 6 else "#cc7a00" for v in vals]
    ax.barh(np.arange(len(labels)), vals, color=colors)
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Order-sensitive pairs requiring fallback (%)")
    ax.set_title("Ranker weakness localizes to comparative change semantics")
    ax.grid(axis="x", alpha=0.2)
    save(fig, "ranker_task_sensitivity.pdf")


def paired_effects() -> None:
    path = ROOT / "runs/dissertation_rigor_20260621/paired_mcnemar_tests.csv"
    wanted = [
        ("Dev schema-only", "Dev metadata", "Full"),
        ("Dev metadata", "Dev final policy", "Full"),
        ("Dev metadata", "Dev final policy", "Answer."),
        ("Test planner", "Test final policy", "Full"),
        ("Test planner", "Test final policy", "Answer."),
        ("Test planner", "Test final policy", "Temp. filter"),
    ]
    data = []
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for a, b, metric in wanted:
        row = next(r for r in rows if r["a"] == a and r["b"] == b and r["metric"] == metric)
        data.append((f"{a.replace('Dev ', '').replace('Test ', '')}\n→ {b.replace('Dev ', '').replace('Test ', '')}\n{metric}", float(row["delta_b_minus_a"])))

    labels, vals = zip(*data)
    fig, ax = plt.subplots(figsize=(8.3, 3.7))
    colors = ["#0072b2" if v >= 0 else "#cc7a00" for v in vals]
    ax.bar(np.arange(len(vals)), vals, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Matched-record gain (points)")
    ax.set_xticks(np.arange(len(vals)))
    ax.set_xticklabels(labels)
    ax.set_title("Paired tests show which gains are substantive")
    ax.grid(axis="y", alpha=0.2)
    save(fig, "paired_effects_synthesis.pdf")


def hypothesis_map() -> None:
    rows = [
        ("H1 Intent bottleneck", "Prompt-only fails despite JSON validity", "Supported"),
        ("H2 Temporal support", "Metadata adds +11.0 temporal-filter pts", "Supported"),
        ("H3 Safety", "Gate gives low false plot without over-refusal", "Supported"),
        ("H4 Hard negatives", "Ranker >98% pairwise, but order sensitivity remains", "Supported w/ caveat"),
        ("H5 Architecture", "Rank/layer placement changes temporal and safety behavior", "Supported"),
        ("Robustness", "Vietnamese/non-WB lower full intent", "Open"),
    ]
    fig, ax = plt.subplots(figsize=(8.5, 3.9))
    ax.axis("off")
    y_positions = np.linspace(0.88, 0.12, len(rows))
    for y, (h, evidence, status) in zip(y_positions, rows):
        color = "#0072b2" if status == "Supported" else ("#cc7a00" if "caveat" in status else "#8b8b8b")
        ax.scatter(0.03, y, s=260, color=color, alpha=0.9)
        ax.text(0.08, y, h, va="center", fontweight="bold")
        ax.text(0.38, y, evidence, va="center")
        ax.text(0.93, y, status, va="center", ha="right", color=color, fontweight="bold")
        ax.plot([0.06, 0.91], [y - 0.055, y - 0.055], color="#dddddd", linewidth=0.6)
    ax.set_title("Synthesis: completed experiments answer different hypotheses", pad=12)
    save(fig, "hypothesis_evidence_map.pdf")


def prompt_vs_adaptation_gap() -> None:
    labels = ["Prompt-only\nfamilies", "Schema\nLoRA", "Metadata\nLoRA", "Unsupported\nx4"]
    json_ok = [99.38, 100.0, 100.0, 100.0]
    full = [0.0, 62.5, 85.94, 87.5]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.8, 3.3))
    ax.plot(x, json_ok, marker="o", label="JSON validity", linewidth=2.0)
    ax.plot(x, full, marker="s", label="Full intent", linewidth=2.0)
    ax.set_ylim(-4, 105)
    ax.set_ylabel("Dev64 score (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Format compliance and analytical intent are different phenomena")
    ax.grid(axis="y", alpha=0.22)
    ax.legend(frameon=False, loc="lower right")
    save(fig, "prompt_vs_adaptation_gap.pdf")


def main() -> None:
    style()
    architecture_cascade()
    safety_frontier()
    adapter_landscape()
    robustness_generalization()
    ranker_sensitivity()
    paired_effects()
    hypothesis_map()
    prompt_vs_adaptation_gap()


if __name__ == "__main__":
    main()
