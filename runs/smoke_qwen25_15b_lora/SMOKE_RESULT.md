# Smoke Fine-Tune Result: Qwen2.5 1.5B LoRA

Date: 2026-06-19

## Model

Base model:

```text
mlx-community/Qwen2.5-1.5B-Instruct-4bit
```

Adapter:

```text
training/adapters/qwen25_15b_ft_tip_smoke
```

## Training Setup

- Fine-tune type: LoRA
- Iterations: 100
- Batch size: 1
- Learning rate: `1e-5`
- Max sequence length: 2048
- Prompt masking: enabled
- Seed: 20260619
- Trainable parameters: 5.276M / 1543.714M, or 0.342%
- Peak memory: about 2.47 GB

## Loss Trace

| Iteration | Train Loss | Validation Loss |
| ---: | ---: | ---: |
| 1 | | 2.086 |
| 10 | 1.117 | |
| 20 | 0.198 | |
| 30 | 0.181 | |
| 40 | 0.082 | |
| 50 | 0.074 | 0.059 |
| 60 | 0.047 | |
| 70 | 0.045 | |
| 80 | 0.023 | |
| 90 | 0.017 | |
| 100 | 0.014 | 0.008 |

Test evaluation over 20 batches:

```text
Test loss 0.014, Test ppl 1.014.
```

## Full Dev Structured Evaluation

The smoke adapter was evaluated on all 184 Paper 09 dev records with structured
intent metrics.

| Metric | Score |
| --- | ---: |
| JSON validity | 100.00% |
| answerability accuracy | 82.61% |
| task-type accuracy | 64.13% |
| required-field F1 | 0.8261 |
| time-field accuracy | 82.61% |
| measure accuracy | 82.61% |
| temporal-filter accuracy | 80.43% |
| statistic accuracy | 89.67% |
| core-intent accuracy | 61.41% |
| full-intent accuracy | 57.07% |

Output files:

```text
dev_adapter_outputs.jsonl
dev_adapter_summary.json
```

This is the first meaningful method signal for Paper 09. It should be treated
as a smoke fine-tune result, not the final paper result, because the run used
only 100 LoRA iterations and no hard negatives.

## Qualitative Smoke Case

Test sample:

```text
timestat_00139
dataset: wb_asean_gdp_current_usd
task_type: temporal_trend
answerability: answerable
```

Base model output:

```json
{
  "intent": "Show the trend of GDP current USD in Indonesia over time",
  "type": "time series",
  "dimension": "year",
  "measure": "gdp_current_usd"
}
```

Adapter output:

```json
{"aggregation": "none", "answerability": "answerable", "chart_type": "line", "group_by": "country", "measure": "gdp_current_usd", "required_fields": ["country", "gdp_current_usd", "year"], "secondary_measure": "", "sort": "none", "statistic": "trend", "task_type": "temporal_trend", "temporal_filter": "all_years", "temporal_granularity": "year", "time_field": "year", "top_k": null, "unsupported_reason": ""}
```

Gold output:

```json
{"aggregation": "none", "answerability": "answerable", "chart_type": "line", "group_by": "country", "measure": "gdp_current_usd", "required_fields": ["country", "gdp_current_usd", "year"], "secondary_measure": "", "sort": "none", "statistic": "trend", "task_type": "temporal_trend", "temporal_filter": "all_years", "temporal_granularity": "year", "time_field": "year", "top_k": null, "unsupported_reason": ""}
```

## Interpretation

The smoke run confirms that the Paper 09 fine-tuning stack works end to end:

- MLX-LM can train on the Paper 09 chat-format SFT data.
- LoRA adapters are saved correctly.
- The fine-tuned adapter can produce the intended structured JSON schema.
- On the inspected smoke case, the adapter exactly matches the gold intent,
  while the base model emits a much looser intent object.
- On the full dev split, the adapter reaches 61.41% core-intent accuracy and
  57.07% full-intent accuracy, suggesting that intent-level fine-tuning is a
  viable method direction.

This is not yet the final scientific evaluation. The next step is error
analysis, hard-negative construction, and a longer full fine-tune.
