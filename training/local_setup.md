# Local Fine-Tuning Setup Notes

## Machine Snapshot

- Hardware: Apple M4 Max
- Memory: about 48 GB
- OS: macOS / Darwin arm64

## Current Local Ollama Models

Available families include:

- Qwen / Qwen-Coder: `qwen2.5:3b`, `qwen2.5-coder:1.5b`, `3b`, `7b`, `14b`, `32b`, `qwen3:4b`
- Llama: `llama3.2:3b`
- Gemma: `gemma3:4b`
- Phi: `phi3:mini`
- DeepSeek: `deepseek-coder:6.7b`
- Vision models: Qwen-VL, LLaVA, MiniCPM-V, Moondream, Granite vision

Ollama models are useful for baseline inference and cross-family comparison.
Fine-tuning will likely need separate Hugging Face or MLX-format weights.

## Installed Fine-Tuning Environment

Homebrew Python 3.11 was installed at:

```text
/opt/homebrew/bin/python3.11
```

A dedicated virtual environment was created at:

```text
manuscripts/09_finetuned_temporal_intent_planner_nl2vis/.venv
```

Installed and verified:

- `mlx==0.31.2`
- `mlx-lm==0.31.3`
- `datasets==5.0.0`
- `pandas==3.0.3`
- `scikit-learn==1.9.0`
- `transformers==5.12.1`

The resolved package list is stored in:

```text
training/requirements-mlx.txt
```

Activate the environment from the workspace root with:

```bash
source manuscripts/09_finetuned_temporal_intent_planner_nl2vis/.venv/bin/activate
```

Check MLX-LM with:

```bash
python -m mlx_lm --help
python -m mlx_lm lora --help
```

MLX sees the GPU device:

```text
Device(gpu, 0)
```

## Recommended Fine-Tuning Path

For this Apple Silicon machine, start with MLX/MLX-LM:

1. install a dedicated environment for Paper 09;
2. fine-tune a small Qwen or Gemma model using LoRA;
3. export or run inference from the fine-tuned adapter;
4. compare against Ollama prompt-only baselines.

Recommended first target:

- Qwen2.5/Qwen3 small model for structured JSON intent planning.

Recommended second target:

- Gemma small model, because Paper 08 showed strong field grounding behavior
  from the Gemma/CodeGemma family.

## Why Not Start With A Large Model

The first experiment should validate the mathematical claim and training
protocol. A small stable model is better for rapid iteration. Once the pipeline
is correct, scale to a larger Qwen/Gemma model only if it adds scientific value.

## Paper 09 MLX Data Directory

MLX-LM expects files named `train.jsonl`, `valid.jsonl`, and `test.jsonl`.
These are linked here:

```text
training/mlx_data/train.jsonl -> ../../benchmark/paper09_train_sft.jsonl
training/mlx_data/valid.jsonl -> ../../benchmark/paper09_dev_sft.jsonl
training/mlx_data/test.jsonl -> ../../benchmark/paper09_test_sft.jsonl
```

## Smoke Fine-Tune Command Template

After choosing a Hugging Face or local MLX-compatible model:

```bash
source manuscripts/09_finetuned_temporal_intent_planner_nl2vis/.venv/bin/activate

python -m mlx_lm lora \
  --model <hf-or-local-model> \
  --train \
  --data manuscripts/09_finetuned_temporal_intent_planner_nl2vis/training/mlx_data \
  --adapter-path manuscripts/09_finetuned_temporal_intent_planner_nl2vis/training/adapters/ft_tip_smoke \
  --iters 100 \
  --batch-size 1 \
  --learning-rate 1e-5 \
  --steps-per-report 10 \
  --steps-per-eval 50 \
  --val-batches 10 \
  --mask-prompt
```
