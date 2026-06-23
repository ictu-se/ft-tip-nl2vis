#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PAPER="$ROOT/manuscripts/09_finetuned_temporal_intent_planner_nl2vis"
PY="$PAPER/.venv/bin/python"
RUN_ROOT="$PAPER/runs/dissertation_strength_20260621"
LOG="$RUN_ROOT/run.log"

mkdir -p "$RUN_ROOT"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG"
}

run_prompt_baseline() {
  local model="$1"
  local safe_name="$2"
  local outdir="$RUN_ROOT/prompt_${safe_name}_dev64"
  mkdir -p "$outdir"
  log "START prompt baseline model=${model}"
  "$PY" "$PAPER/scripts/run_ollama_intent_inference.py" \
    --model "$model" \
    --input "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl" \
    --output "$outdir/dev64_outputs.jsonl" \
    --summary "$outdir/dev64_summary.json" \
    --limit 64 \
    --timeout 300 \
    --progress-every 8 \
    --resume >>"$LOG" 2>&1
  log "END prompt baseline model=${model} exit=$?"
}

write_lora_config() {
  local config="$1"
  local adapter="$2"
  local rank="$3"
  local layers="$4"
  local seed="$5"
  "$PY" - "$config" "$adapter" "$rank" "$layers" "$seed" "$PAPER" <<'PY'
import sys
from pathlib import Path

config = Path(sys.argv[1])
adapter = sys.argv[2]
rank = int(sys.argv[3])
layers = int(sys.argv[4])
seed = int(sys.argv[5])
paper = Path(sys.argv[6])

text = f"""model: mlx-community/Qwen2.5-1.5B-Instruct-4bit
train: true
fine_tune_type: lora
optimizer: adam
data: {paper / 'training/mlx_expanded_metadata_smoke'}
seed: {seed}
num_layers: {layers}
batch_size: 1
iters: 300
val_batches: 128
learning_rate: 1e-5
steps_per_report: 50
steps_per_eval: 100
adapter_path: {adapter}
save_every: 100
test: false
test_batches: 500
max_seq_length: 2048
grad_checkpoint: false
grad_accumulation_steps: 1
clear_cache_threshold: 0
mask_prompt: true
lora_parameters:
  rank: {rank}
  dropout: 0.0
  scale: 20.0
"""
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(text, encoding="utf-8")
PY
}

run_lora_variant() {
  local name="$1"
  local rank="$2"
  local layers="$3"
  local seed="$4"
  local adapter="$PAPER/training/adapters/${name}"
  local outdir="$RUN_ROOT/${name}"
  local config="$RUN_ROOT/configs/${name}.yaml"
  mkdir -p "$outdir"
  write_lora_config "$config" "$adapter" "$rank" "$layers" "$seed"

  if [ ! -f "$adapter/adapters.safetensors" ]; then
    log "START LoRA ablation name=${name} rank=${rank} layers=${layers}"
    "$PY" -m mlx_lm lora -c "$config" >>"$LOG" 2>&1
    log "END LoRA ablation name=${name} exit=$?"
  else
    log "SKIP train existing adapter ${name}"
  fi

  log "START dev64 eval name=${name}"
  "$PY" "$PAPER/scripts/run_mlx_intent_inference.py" \
    --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
    --adapter-path "$adapter" \
    --input "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl" \
    --output "$outdir/dev64_outputs.jsonl" \
    --summary "$outdir/dev64_summary.json" \
    --limit 64 \
    --max-tokens 180 \
    --temp 0.0 \
    --progress-every 16 \
    --resume >>"$LOG" 2>&1
  log "END dev64 eval name=${name} exit=$?"
}

log "Dissertation-strength experiment runner started."

run_prompt_baseline "llama3.2:3b" "llama32_3b"
run_prompt_baseline "qwen2.5:3b" "qwen25_3b"
run_prompt_baseline "qwen2.5-coder:7b" "qwen25_coder_7b"
run_prompt_baseline "qwen3:4b" "qwen3_4b"

run_lora_variant "qwen25_15b_expanded_metadata_rank4_l16" 4 16 20260621
run_lora_variant "qwen25_15b_expanded_metadata_rank16_l16" 16 16 20260622
run_lora_variant "qwen25_15b_expanded_metadata_rank32_l16" 32 16 20260623
run_lora_variant "qwen25_15b_expanded_metadata_rank8_l8" 8 8 20260624
run_lora_variant "qwen25_15b_expanded_metadata_rank8_all_layers" 8 -1 20260625

log "Dissertation-strength experiment runner finished."
