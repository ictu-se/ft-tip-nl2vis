# Prompt-Only Dev64 Baseline Result

## Purpose

This experiment tests whether prompt-only local models can follow the Paper 09
structured intent schema without fine-tuning. It uses the same expanded dev64
slice and temporal-metadata-aware prompt representation used by the LoRA smoke
evaluations.

## Models

- `mlx-community/Qwen2.5-1.5B-Instruct-4bit` through MLX-LM, no adapter.
- `gemma3:4b` through local Ollama.
- `phi3:mini` through local Ollama.
- `deepseek-coder:6.7b` through local Ollama.

## Dev64 Metrics

| Variant | JSON | Answerability | Temporal filter | Core intent | Full intent |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B prompt-only | 100.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Gemma3-4B prompt-only | 100.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Phi3-mini prompt-only | 93.75% | 0.00% | 0.00% | 0.00% | 0.00% |
| DeepSeek-Coder-6.7B prompt-only | 100.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Schema-only LoRA | 100.00% | 87.50% | 68.75% | 62.50% | 62.50% |
| Metadata-aware LoRA | 100.00% | 87.50% | 96.875% | 87.50% | 85.9375% |
| Unsupported-x4 LoRA | 100.00% | 100.00% | 92.1875% | 87.50% | 87.50% |

## Interpretation

The prompt-only models either emit syntactically valid JSON that does not match
the target intent schema, or fail JSON validity on a minority of examples. Qwen
often outputs schema-like JSON objects, Gemma outputs query fragments such as a
country and year list, Phi emits nested generic "intent" descriptions, and
DeepSeek-Coder often emits chart-planning JSON rather than the required
analytical intent schema. This is exactly the failure mode Paper 09 argues
against: format validity is not analytical intent faithfulness.

The LoRA adapters do not merely improve JSON validity, because JSON validity is
already 100% for prompt-only models. They learn the task-specific intent schema
and temporal/statistical commitments.
