# FT-TIP NL2Vis Reproducibility Package

This repository contains the code, benchmark splits, and experimental artifacts for:

**Temporal-Statistical Intent Planning for Natural Language to Visualization under Support Metadata**

The manuscript source and manuscript PDF are intentionally excluded. This repository is meant for reproducibility review, GitHub archival, and Zenodo DOI citation.

## Contents

- `scripts/`: corpus construction, inference, evaluation, ablation, audit, and figure-generation scripts.
- `benchmark/`: original Paper 09 train/dev/test splits.
- `benchmark_expanded/`: expanded CSV-backed corpus, schema-only and temporal-metadata SFT splits, and temporal hard-negative ranking pairs.
- `benchmark_optional_audits/`: optional Vietnamese-diacritic and non-World-Bank audit splits.
- `training/`: training notes, requirements, tiny prototype data, and adapter metadata. Model weight files are excluded from GitHub.
- `runs/`: frozen-test outputs, prompt baselines, ablations, ranker/verifier outputs, chart-level audit, rule-based baseline, and statistical-rigor artifacts.
- `figures/`: generated result figures and Mermaid architecture source used for reporting.
- `docs/`: frozen command logs and reproducibility checklist.
- `zenodo/`: Zenodo metadata and release checklist.

## Reproducing Key Results

The frozen final-test command is documented in:

```text
docs/FINAL_TEST_COMMANDS.md
```

The main command sequence is:

```bash
bash scripts/run_final_test_once.sh
python3 scripts/build_dissertation_rigor_package.py
python3 scripts/evaluate_chart_level_intents.py
```

The original experiments used local MLX/Ollama components and Qwen2.5-family LoRA adapters. The repository includes exact inputs and outputs used for the reported tables; adapter weight files are not committed to GitHub because they are binary checkpoints and should be attached as Zenodo release assets if public weight reproduction is required.

## Important Results

Frozen expanded-test results are under:

```text
runs/final_test_20260620/
```

Statistical confidence intervals, paired tests, slice matrices, and generated reporting artifacts are under:

```text
runs/dissertation_rigor_20260621/
```

Chart-level audit artifacts are under:

```text
runs/chart_level_audit_20260621/
```

## GitHub and Zenodo Archive

The archived release is available at Zenodo:

https://doi.org/10.5281/zenodo.20819042

## Exclusions

The following are intentionally excluded:

- manuscript LaTeX source and manuscript PDFs;
- Elsevier template files;
- editor-sample PDFs and literature PDFs;
- local virtual environments and caches;
- binary model checkpoints such as `.safetensors`.

## Citation

Please cite the archived Zenodo release:

Nguyen, T. V. (2026). FT-TIP NL2Vis Reproducibility Package (v1.0.1). Zenodo. https://doi.org/10.5281/zenodo.20819042
