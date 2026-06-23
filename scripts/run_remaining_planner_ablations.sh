#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PAPER="$ROOT/manuscripts/09_finetuned_temporal_intent_planner_nl2vis"
PY="$PAPER/.venv/bin/python"
RUN_ROOT="$PAPER/runs/remaining_planner_ablations_20260621"
LOG="$RUN_ROOT/run.log"
TRAIN_SRC="$PAPER/benchmark_expanded/paper09_expanded_train_with_temporal_metadata_sft.jsonl"
DEV_SRC="$PAPER/benchmark_expanded/paper09_expanded_dev_with_temporal_metadata_sft.jsonl"
BASE_MODEL="mlx-community/Qwen2.5-1.5B-Instruct-4bit"

mkdir -p "$RUN_ROOT"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG"
}

prepare_data() {
  "$PY" - "$PAPER" "$TRAIN_SRC" "$DEV_SRC" <<'PY'
import json
import sys
from pathlib import Path

paper = Path(sys.argv[1])
train_src = Path(sys.argv[2])
dev_src = Path(sys.argv[3])

def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

train = read_jsonl(train_src)
dev = read_jsonl(dev_src)
dev512 = dev[:512]

variants = {
    "mlx_metadata_answerable_only": [r for r in train if r.get("answerability") == "answerable"],
    "mlx_metadata_english_only": [r for r in train if r.get("language") == "en"],
}

for name, rows in variants.items():
    out = paper / "training" / name
    write_jsonl(out / "train.jsonl", rows)
    write_jsonl(out / "valid.jsonl", dev512)
    write_jsonl(out / "test.jsonl", dev512)
    summary = {
        "variant": name,
        "train_records": len(rows),
        "valid_records": len(dev512),
        "test_records": len(dev512),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
PY
}

write_config() {
  local config="$1"
  local data_dir="$2"
  local adapter="$3"
  local seed="$4"
  local mask_prompt="$5"
  "$PY" - "$config" "$data_dir" "$adapter" "$seed" "$mask_prompt" "$BASE_MODEL" <<'PY'
import sys
from pathlib import Path

config = Path(sys.argv[1])
data_dir = sys.argv[2]
adapter = sys.argv[3]
seed = int(sys.argv[4])
mask_prompt = sys.argv[5].lower()
model = sys.argv[6]

text = f"""model: {model}
train: true
fine_tune_type: lora
optimizer: adam
data: {data_dir}
seed: {seed}
num_layers: 16
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
mask_prompt: {mask_prompt}
lora_parameters:
  rank: 8
  dropout: 0.0
  scale: 20.0
"""
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(text, encoding="utf-8")
PY
}

run_variant() {
  local name="$1"
  local data_dir="$2"
  local seed="$3"
  local mask_prompt="$4"
  local adapter="$PAPER/training/adapters/$name"
  local outdir="$RUN_ROOT/$name"
  local config="$RUN_ROOT/configs/$name.yaml"
  mkdir -p "$outdir"
  write_config "$config" "$data_dir" "$adapter" "$seed" "$mask_prompt"

  if [ ! -f "$adapter/adapters.safetensors" ]; then
    log "START train ${name}"
    "$PY" -m mlx_lm lora -c "$config" >>"$LOG" 2>&1
    log "END train ${name} exit=$?"
  else
    log "SKIP train existing adapter ${name}"
  fi

  log "START dev64 eval ${name}"
  "$PY" "$PAPER/scripts/run_mlx_intent_inference.py" \
    --model "$BASE_MODEL" \
    --adapter-path "$adapter" \
    --input "$DEV_SRC" \
    --output "$outdir/dev64_outputs.jsonl" \
    --summary "$outdir/dev64_summary.json" \
    --limit 64 \
    --max-tokens 180 \
    --temp 0.0 \
    --progress-every 16 \
    --resume >>"$LOG" 2>&1
  log "END dev64 eval ${name} exit=$?"
}

log "Remaining planner ablations started."
prepare_data
run_variant "qwen25_15b_metadata_answerable_only" "$PAPER/training/mlx_metadata_answerable_only" 20260626 true
run_variant "qwen25_15b_metadata_no_prompt_mask" "$PAPER/training/mlx_expanded_metadata_smoke" 20260627 false
run_variant "qwen25_15b_metadata_english_only" "$PAPER/training/mlx_metadata_english_only" 20260628 true
log "Remaining planner ablations finished."
