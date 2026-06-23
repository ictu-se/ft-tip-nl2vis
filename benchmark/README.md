# Benchmark Notes

Paper 09 reuses TimeStat-NL2Vis from Paper 08 as the starting supervision set,
but it must create its own frozen train/dev/test split.

Source file:

```text
../08_temporal_statistical_intent_nl2vis/benchmark/temporal_stat_tasks.jsonl
```

Do not evaluate on examples used for fine-tuning.

Required derived files:

- `paper09_train.jsonl`
- `paper09_dev.jsonl`
- `paper09_test.jsonl`
- `paper09_hard_negative_test.jsonl`

