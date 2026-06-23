# Expanded Paper 09 TimeStat Corpus

This corpus is generated from local CSV files and dataset metadata. It is intended for the serious Paper 09 ablation plan: schema-only SFT, temporal-metadata-aware SFT, and hard-negative temporal ranking.

## Corpus Size

- Inventoried metadata datasets: 783
- Usable datasets: 783
- Intent records: 21153
- Hard-negative ranking pairs: 60340

## Split Summary

- train: 14773 records, 547 datasets
- dev: 3269 records, 121 datasets
- test: 3111 records, 115 datasets

## Top Domains

- worldbank_expansion: 19521
- economy: 355
- health: 326
- population: 191
- education: 164
- technology: 162
- environment: 108
- labor: 81
- energy: 81
- transport: 54
- finance: 54
- labor_technology: 29
- tourism: 27

## Sources

- World Bank Indicators API expansion: 19521
- World Bank Indicators API: 1404
- Derived from World Bank/OWID normalized tables: 174
- Our World in Data Grapher API: 54

## Scientific Use

- Use `*_schema_only_sft.jsonl` to test whether the model can infer temporal bounds from schema alone.
- Use `*_with_temporal_metadata_sft.jsonl` to test the proposed temporal-grounding-aware planner.
- Use `*_ranking_pairs.jsonl` for the hard-negative objective and ablation of temporal-boundary reasoning.
- Keep the expanded test split untouched until the training and checkpoint-selection protocol is frozen.
