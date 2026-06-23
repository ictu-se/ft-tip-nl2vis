# Scripts To Build

Planned scripts:

- `build_sft_dataset.py`: convert TimeStat-NL2Vis JSONL to instruction-tuning JSONL.
- `split_timestat_groups.py`: grouped train/dev/test split by dataset and task type.
- `run_finetuned_planner.py`: inference wrapper for the fine-tuned model.
- `evaluate_intent_outputs.py`: structured intent metrics.
- `build_paper09_report.py`: tables and Markdown reports.

Use deterministic code only for data conversion, metric computation, reporting,
and reproducibility infrastructure. The substantive method should remain
model-based and fine-tuned, not rule-based.

