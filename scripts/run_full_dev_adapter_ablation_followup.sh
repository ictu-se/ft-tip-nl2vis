#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PAPER="$ROOT/manuscripts/09_finetuned_temporal_intent_planner_nl2vis"
PY="$PAPER/.venv/bin/python"
INFER="$PAPER/scripts/run_mlx_intent_inference.py"
RUN_ROOT="$PAPER/runs/dissertation_strength_20260621"
LOG="$RUN_ROOT/full_dev_followup.log"
INPUT="$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl"

mkdir -p "$RUN_ROOT"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG"
}

run_full_dev() {
  local name="$1"
  local adapter="$PAPER/training/adapters/$name"
  local outdir="$RUN_ROOT/${name}_full_dev"
  mkdir -p "$outdir"

  log "START full-dev eval name=${name}"
  "$PY" "$INFER" \
    --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
    --adapter-path "$adapter" \
    --input "$INPUT" \
    --output "$outdir/full_dev_outputs.jsonl" \
    --summary "$outdir/full_dev_summary.json" \
    --max-tokens 180 \
    --temp 0.0 \
    --progress-every 50 \
    --resume >>"$LOG" 2>&1
  log "END full-dev eval name=${name} exit=$? rows=$(wc -l < "$outdir/full_dev_outputs.jsonl" 2>/dev/null || echo 0)"
}

log "Full-dev adapter ablation follow-up started."
run_full_dev "qwen25_15b_expanded_metadata_rank8_all_layers"
run_full_dev "qwen25_15b_expanded_metadata_rank16_l16"
log "Full-dev adapter ablation follow-up finished."
