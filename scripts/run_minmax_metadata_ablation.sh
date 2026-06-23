#!/usr/bin/env bash
set -u

PAPER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$PAPER/.venv/bin/python"
RUN_ROOT="$PAPER/runs/minmax_metadata_ablation_20260621"
LOG="$RUN_ROOT/run.log"
ADAPTER="$PAPER/training/adapters/qwen25_15b_expanded_minmax_metadata_rank8_l16"
CONFIG="$RUN_ROOT/minmax_rank8_l16.yaml"

mkdir -p "$RUN_ROOT" "$RUN_ROOT/configs"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG"
}

cat >"$CONFIG" <<YAML
model: mlx-community/Qwen2.5-1.5B-Instruct-4bit
train: true
fine_tune_type: lora
optimizer: adam
data: $PAPER/training/mlx_expanded_minmax_metadata
seed: 20260626
num_layers: 16
batch_size: 1
iters: 300
val_batches: 128
learning_rate: 1e-5
steps_per_report: 50
steps_per_eval: 100
adapter_path: $ADAPTER
save_every: 100
test: false
test_batches: 500
max_seq_length: 2048
grad_checkpoint: false
grad_accumulation_steps: 1
clear_cache_threshold: 0
mask_prompt: true
lora_parameters:
  rank: 8
  dropout: 0.0
  scale: 20.0
YAML

log "Min/max metadata ablation started."

if [ ! -f "$ADAPTER/adapters.safetensors" ]; then
  log "START train minmax rank8 last16"
  "$PY" -m mlx_lm lora -c "$CONFIG" >>"$LOG" 2>&1
  log "END train minmax rank8 last16 exit=$?"
else
  log "SKIP train existing adapter $ADAPTER"
fi

log "START dev64 eval"
"$PY" "$PAPER/scripts/run_mlx_intent_inference.py" \
  --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
  --adapter-path "$ADAPTER" \
  --input "$PAPER/benchmark_expanded/paper09_expanded_dev_minmax_metadata_sft.jsonl" \
  --output "$RUN_ROOT/dev64_outputs.jsonl" \
  --summary "$RUN_ROOT/dev64_summary.json" \
  --limit 64 \
  --max-tokens 180 \
  --temp 0.0 \
  --progress-every 16 \
  --resume >>"$LOG" 2>&1
log "END dev64 eval exit=$?"

log "START full-dev eval"
"$PY" "$PAPER/scripts/run_mlx_intent_inference.py" \
  --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
  --adapter-path "$ADAPTER" \
  --input "$PAPER/benchmark_expanded/paper09_expanded_dev_minmax_metadata_sft.jsonl" \
  --output "$RUN_ROOT/full_dev_outputs.jsonl" \
  --summary "$RUN_ROOT/full_dev_summary.json" \
  --max-tokens 180 \
  --temp 0.0 \
  --progress-every 128 \
  --resume >>"$LOG" 2>&1
log "END full-dev eval exit=$?"

log "Min/max metadata ablation finished."
