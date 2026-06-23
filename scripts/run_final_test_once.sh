#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PAPER_DIR"

RUN_DIR="runs/final_test_20260620"
TEST_ARTIFACT_DIR="training/gate_ranker_test_artifacts"
MODEL="mlx-community/Qwen2.5-1.5B-Instruct-4bit"

mkdir -p "$RUN_DIR"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')" "$*"
}

log "Building gate/ranker test artifacts"
.venv/bin/python scripts/build_gate_ranker_test_artifacts.py \
  --benchmark-dir benchmark_expanded \
  --out-dir "$TEST_ARTIFACT_DIR" \
  --seed 20260620

log "Running planner test inference"
.venv/bin/python scripts/run_mlx_intent_inference.py \
  --model "$MODEL" \
  --adapter-path training/adapters/qwen25_15b_expanded_metadata_smoke \
  --input benchmark_expanded/paper09_expanded_test_with_temporal_metadata_sft.jsonl \
  --output "$RUN_DIR/planner_test_outputs.jsonl" \
  --summary "$RUN_DIR/planner_test_summary.json" \
  --max-tokens 260 \
  --temp 0.0 \
  --progress-every 100 \
  --resume

log "Running gate test inference"
.venv/bin/python scripts/run_mlx_gate_inference.py \
  --model "$MODEL" \
  --adapter-path training/adapters/qwen25_15b_gate_balanced_smoke \
  --input "$TEST_ARTIFACT_DIR/gate_test.jsonl" \
  --output "$RUN_DIR/gate_test_outputs.jsonl" \
  --summary "$RUN_DIR/gate_test_summary.json" \
  --max-tokens 96 \
  --temp 0.0 \
  --progress-every 100 \
  --resume

log "Composing planner+gate test policy"
.venv/bin/python scripts/evaluate_composed_policy.py \
  --planner "$RUN_DIR/planner_test_outputs.jsonl" \
  --gate "$RUN_DIR/gate_test_outputs.jsonl" \
  --output "$RUN_DIR/composed_planner_gate_test_outputs.jsonl" \
  --summary "$RUN_DIR/composed_planner_gate_test_summary.json"

log "Applying temporal-constrained test policy"
.venv/bin/python scripts/evaluate_temporal_constrained_policy.py \
  --composed "$RUN_DIR/composed_planner_gate_test_outputs.jsonl" \
  --dev-records benchmark_expanded/paper09_expanded_test.jsonl \
  --output "$RUN_DIR/composed_planner_gate_temporal_constrained_test_outputs.jsonl" \
  --summary "$RUN_DIR/composed_planner_gate_temporal_constrained_test_summary.json"

log "Running original-order ranker test inference"
.venv/bin/python scripts/run_mlx_ranker_inference.py \
  --model "$MODEL" \
  --adapter-path training/adapters/qwen25_15b_ranker_hard_negative_smoke \
  --input "$TEST_ARTIFACT_DIR/ranker_test.jsonl" \
  --output "$RUN_DIR/ranker_test_outputs.jsonl" \
  --summary "$RUN_DIR/ranker_test_summary.json" \
  --max-tokens 96 \
  --temp 0.0 \
  --progress-every 100 \
  --resume

log "Building swapped-order ranker test set"
.venv/bin/python scripts/build_swapped_ranker_eval.py \
  --input "$TEST_ARTIFACT_DIR/ranker_test.jsonl" \
  --output "$TEST_ARTIFACT_DIR/ranker_test_swapped.jsonl"

log "Running swapped-order ranker test inference"
.venv/bin/python scripts/run_mlx_ranker_inference.py \
  --model "$MODEL" \
  --adapter-path training/adapters/qwen25_15b_ranker_hard_negative_smoke \
  --input "$TEST_ARTIFACT_DIR/ranker_test_swapped.jsonl" \
  --output "$RUN_DIR/ranker_test_swapped_outputs.jsonl" \
  --summary "$RUN_DIR/ranker_test_swapped_summary.json" \
  --max-tokens 96 \
  --temp 0.0 \
  --progress-every 100 \
  --resume

log "Analyzing ranker position bias on test"
.venv/bin/python scripts/analyze_ranker_position_bias.py \
  --original "$RUN_DIR/ranker_test_outputs.jsonl" \
  --swapped "$RUN_DIR/ranker_test_swapped_outputs.jsonl" \
  --out-dir "$RUN_DIR/ranker_position_bias"

log "Evaluating symmetric ranker test policy"
.venv/bin/python scripts/evaluate_symmetric_ranker_policy.py \
  --original "$RUN_DIR/ranker_test_outputs.jsonl" \
  --swapped "$RUN_DIR/ranker_test_swapped_outputs.jsonl" \
  --out-dir "$RUN_DIR/symmetric_ranker_policy"

log "Final test run complete"
