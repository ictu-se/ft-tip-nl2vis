#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PAPER="$ROOT/manuscripts/09_finetuned_temporal_intent_planner_nl2vis"
PY="$PAPER/.venv/bin/python"
RUN_ROOT="$PAPER/runs/optional_external_multilingual_20260621"
LOG="$RUN_ROOT/run.log"
BASE_MODEL="mlx-community/Qwen2.5-1.5B-Instruct-4bit"
PLANNER_ADAPTER="$PAPER/training/adapters/qwen25_15b_expanded_metadata_smoke"

mkdir -p "$RUN_ROOT"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG"
}

log "Optional external/multilingual audit runner started."

log "START optional Mistral pull"
ollama pull mistral:7b >>"$LOG" 2>&1
log "END optional Mistral pull exit=$?"

log "START Mistral prompt-only dev64 smoke"
"$PY" "$PAPER/scripts/run_ollama_intent_inference.py" \
  --model mistral:7b \
  --input "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl" \
  --output "$RUN_ROOT/prompt_mistral_7b_dev64/dev64_outputs.jsonl" \
  --summary "$RUN_ROOT/prompt_mistral_7b_dev64/dev64_summary.json" \
  --limit 64 \
  --timeout 300 \
  --progress-every 8 \
  --resume >>"$LOG" 2>&1
log "END Mistral prompt-only dev64 smoke exit=$?"

log "START build optional audit splits"
"$PY" "$PAPER/scripts/build_optional_audit_splits.py" \
  --raw-dev "$PAPER/benchmark_expanded/paper09_expanded_dev.jsonl" \
  --sft-dev "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl" \
  --out-dir "$PAPER/benchmark_optional_audits" >>"$LOG" 2>&1
log "END build optional audit splits exit=$?"

run_planner_eval() {
  local name="$1"
  local input="$2"
  local outdir="$RUN_ROOT/$name"
  mkdir -p "$outdir"
  log "START planner eval ${name}"
  "$PY" "$PAPER/scripts/run_mlx_intent_inference.py" \
    --model "$BASE_MODEL" \
    --adapter-path "$PLANNER_ADAPTER" \
    --input "$input" \
    --output "$outdir/outputs.jsonl" \
    --summary "$outdir/summary.json" \
    --max-tokens 180 \
    --temp 0.0 \
    --progress-every 50 \
    --resume >>"$LOG" 2>&1
  log "END planner eval ${name} exit=$? rows=$(wc -l < "$outdir/outputs.jsonl" 2>/dev/null || echo 0)"
}

run_planner_eval \
  "planner_vi_diacritic_dev" \
  "$PAPER/benchmark_optional_audits/paper09_dev_vi_diacritic_sft.jsonl"

run_planner_eval \
  "planner_non_worldbank_dev" \
  "$PAPER/benchmark_optional_audits/paper09_dev_non_worldbank_sft.jsonl"

log "Optional external/multilingual audit runner finished."
