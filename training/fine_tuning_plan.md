# Fine-Tuning Plan

## Goal

Fine-tune a local base model to output faithful temporal-statistical intent
plans from `(query, dataset schema)` inputs.

## Candidate Base Models

Start with one practical model, then add cross-family comparisons if compute
allows:

- Qwen/Qwen-Coder family: strong structured output candidate.
- Gemma/CodeGemma family: strong field grounding baseline from Paper 08.
- Llama family: useful compact baseline.
- Mistral family: useful safety/refusal contrast.

The first fine-tuning target should be selected by local availability and stable
training support. A reasonable first target is a small Qwen or Gemma model with
LoRA/QLoRA.

## Training Data

Source:

```text
../08_temporal_statistical_intent_nl2vis/benchmark/temporal_stat_tasks.jsonl
```

Each example becomes an instruction-tuning record:

```json
{
  "instruction": "Infer the temporal-statistical visualization intent...",
  "input": {
    "query": "...",
    "schema": [...]
  },
  "output": {
    "answerability": "...",
    "task_type": "...",
    "required_fields": [...],
    "time_field": "...",
    "measure": "...",
    "temporal_filter": "...",
    "statistic": "..."
  }
}
```

## Split Policy

Avoid random-only leakage. Use grouped splitting:

- group by `dataset_id`;
- preserve language balance;
- preserve answerable/unanswerable ratio;
- preserve task-type coverage.

Initial split:

- train: 70%;
- dev: 15%;
- test: 15%.

The test set must remain untouched until the final evaluation.

## Training Variants

1. `SFT-intent-only`
   Fine-tune the planner to produce gold intent JSON.

2. `SFT-intent-plus-rationale`
   Fine-tune with a short hidden-style reasoning field during training, then
   strip it at inference if needed. Use only if it improves stability.

3. `SFT-with-hard-negatives`
   Add contrastive examples from Paper 08 model failures, especially false
   plotting and temporal-filter mismatch.

4. `Planner-plus-ranker`
   Generate K candidate intents and train a ranker/verifier to choose the best
   candidate.

## Main Metrics

Primary:

- core intent accuracy;
- temporal-filter accuracy;
- statistic accuracy;
- task-type accuracy;
- required-field F1;
- false-plot unanswerable rate;
- over-refusal rate.

Secondary:

- JSON validity;
- schema validity;
- full-intent accuracy;
- language-specific scores;
- task-type-specific scores.

## Baselines

- Prompt-only intent-first models from Paper 08.
- Direct-spec ablation from Paper 08.
- Fine-tuned planner without hard negatives.
- Fine-tuned planner with hard negatives.
- Optional planner-plus-ranker.

## Minimum Publishable Evidence

The method becomes paper-worthy if it shows:

- clear improvement in core-intent accuracy over the best prompt-only baseline;
- improved temporal-filter and statistic accuracy;
- no unacceptable increase in false plotting;
- stable behavior on both English and Vietnamese prompts.

