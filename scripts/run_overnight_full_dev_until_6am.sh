#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PAPER="$ROOT/manuscripts/09_finetuned_temporal_intent_planner_nl2vis"
PY="$PAPER/.venv/bin/python"
INFER="$PAPER/scripts/run_mlx_intent_inference.py"
RUN_ROOT="$PAPER/runs/overnight_full_dev_20260619"
LOG="$RUN_ROOT/overnight.log"

mkdir -p "$RUN_ROOT"

deadline_epoch="$("$PY" - <<'PY'
from datetime import datetime, timedelta
now = datetime.now()
deadline = (now + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
print(int(deadline.timestamp()))
PY
)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG"
}

remaining_seconds() {
  local now_epoch
  now_epoch="$(date +%s)"
  echo $((deadline_epoch - now_epoch))
}

write_partial_summary() {
  local output="$1"
  local summary="$2"
  "$PY" - "$output" "$summary" <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[0]).resolve().parent))

output = Path(sys.argv[1])
summary = Path(sys.argv[2])
if not output.exists():
    raise SystemExit(0)

rows = [json.loads(line) for line in output.open(encoding="utf-8") if line.strip()]
if not rows:
    raise SystemExit(0)

bool_keys = [
    "json_ok",
    "answerability_ok",
    "task_type_ok",
    "time_field_ok",
    "measure_ok",
    "temporal_filter_ok",
    "statistic_ok",
    "core_intent_ok",
    "full_intent_ok",
]
out = {"n": len(rows), "partial": True}
for key in bool_keys:
    out[f"{key}_pct"] = 100 * sum(bool(row.get(key)) for row in rows) / len(rows)
out["required_field_f1"] = sum(float(row.get("required_field_f1", 0.0)) for row in rows) / len(rows)
summary.parent.mkdir(parents=True, exist_ok=True)
summary.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

run_with_deadline() {
  "$@" >>"$LOG" 2>&1 &
  local child=$!
  local now_epoch

  while kill -0 "$child" 2>/dev/null; do
    now_epoch="$(date +%s)"
    if [ "$now_epoch" -ge "$deadline_epoch" ]; then
      log "Deadline reached; stopping child pid=$child."
      kill "$child" 2>/dev/null || true
      sleep 10
      if kill -0 "$child" 2>/dev/null; then
        log "Child pid=$child still alive after SIGTERM; sending SIGKILL."
        kill -9 "$child" 2>/dev/null || true
      fi
      wait "$child" 2>/dev/null
      return 124
    fi
    sleep 30
  done

  wait "$child"
}

run_eval() {
  local name="$1"
  local adapter="$2"
  local input="$3"
  local outdir="$RUN_ROOT/$name"
  local remain
  mkdir -p "$outdir"
  remain="$(remaining_seconds)"
  if [ "$remain" -le 300 ]; then
    log "Skip $name: only ${remain}s remains before 06:00."
    return 0
  fi

  log "START $name with ${remain}s remaining."
  if [ -n "$adapter" ]; then
    run_with_deadline "$PY" "$INFER" \
      --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
      --adapter-path "$adapter" \
      --input "$input" \
      --output "$outdir/full_dev_outputs.jsonl" \
      --summary "$outdir/full_dev_summary.json" \
      --max-tokens 180 \
      --temp 0.0 \
      --progress-every 50 \
      --resume
  else
    run_with_deadline "$PY" "$INFER" \
      --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
      --input "$input" \
      --output "$outdir/full_dev_outputs.jsonl" \
      --summary "$outdir/full_dev_summary.json" \
      --max-tokens 180 \
      --temp 0.0 \
      --progress-every 50 \
      --resume
  fi
  local code=$?
  write_partial_summary "$outdir/full_dev_outputs.jsonl" "$outdir/full_dev_partial_summary.json"
  log "END $name exit_code=$code rows=$(wc -l < "$outdir/full_dev_outputs.jsonl" 2>/dev/null || echo 0)."
  return 0
}

log "Overnight runner started. Deadline epoch=$deadline_epoch ($(date -r "$deadline_epoch" '+%Y-%m-%d %H:%M:%S %Z'))."
log "Workspace: $ROOT"

run_eval \
  "metadata_lora_full_dev" \
  "$PAPER/training/adapters/qwen25_15b_expanded_metadata_smoke" \
  "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl"

run_eval \
  "unsupported_x4_lora_full_dev" \
  "$PAPER/training/adapters/qwen25_15b_expanded_metadata_unsupported_x4_smoke" \
  "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl"

run_eval \
  "schema_only_lora_full_dev" \
  "$PAPER/training/adapters/qwen25_15b_expanded_schema_smoke" \
  "$PAPER/benchmark_expanded/paper09_expanded_dev_schema_only_sft.jsonl"

run_eval \
  "qwen_prompt_only_full_dev_if_time" \
  "" \
  "$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl"

log "Overnight runner finished or reached deadline."
