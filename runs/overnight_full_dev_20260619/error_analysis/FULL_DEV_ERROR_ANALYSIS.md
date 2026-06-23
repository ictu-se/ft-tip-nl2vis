# Paper 09 Full-Dev Error Analysis

This report analyzes the expanded-dev split only. The held-out expanded test split remains untouched.

## Overall Full-Dev Metrics

| run | n | json_ok_pct | answerability_ok_pct | temporal_filter_ok_pct | core_intent_ok_pct | full_intent_ok_pct | false_plot_rate_pct | over_refusal_rate_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| metadata_lora | 3269 | 100.00 | 85.19 | 93.09 | 84.37 | 84.22 | 14.81 | 0.00 |
| qwen_prompt_only | 3269 | 99.30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| schema_only_lora | 3269 | 100.00 | 85.19 | 82.10 | 72.65 | 72.62 | 14.81 | 0.00 |
| unsupported_x4_lora | 3269 | 100.00 | 86.85 | 85.81 | 79.63 | 79.23 | 0.24 | 12.91 |

## Failure Taxonomy

| run | failure_type | count | rate_pct |
| --- | --- | --- | --- |
| metadata_lora | wrong_measure | 486 | 14.87 |
| metadata_lora | false_plot_unanswerable_as_answerable | 484 | 14.81 |
| metadata_lora | wrong_time_field | 484 | 14.81 |
| metadata_lora | wrong_task_type | 376 | 11.50 |
| metadata_lora | wrong_temporal_filter | 226 | 6.91 |
| metadata_lora | wrong_statistic | 32 | 0.98 |
| metadata_lora | core_ok_but_full_wrong | 5 | 0.15 |
| qwen_prompt_only | wrong_statistic | 3246 | 99.30 |
| qwen_prompt_only | wrong_task_type | 3246 | 99.30 |
| qwen_prompt_only | wrong_temporal_filter | 3246 | 99.30 |
| qwen_prompt_only | wrong_measure | 3173 | 97.06 |
| qwen_prompt_only | wrong_time_field | 2984 | 91.28 |
| qwen_prompt_only | invalid_json | 23 | 0.70 |
| schema_only_lora | wrong_temporal_filter | 585 | 17.90 |
| schema_only_lora | wrong_measure | 485 | 14.84 |
| schema_only_lora | false_plot_unanswerable_as_answerable | 484 | 14.81 |
| schema_only_lora | wrong_time_field | 484 | 14.81 |
| schema_only_lora | wrong_task_type | 374 | 11.44 |
| schema_only_lora | wrong_statistic | 30 | 0.92 |
| schema_only_lora | core_ok_but_full_wrong | 1 | 0.03 |
| unsupported_x4_lora | wrong_task_type | 513 | 15.69 |
| unsupported_x4_lora | wrong_temporal_filter | 464 | 14.19 |
| unsupported_x4_lora | wrong_measure | 432 | 13.22 |
| unsupported_x4_lora | wrong_time_field | 430 | 13.15 |
| unsupported_x4_lora | over_refusal_answerable_as_unanswerable | 422 | 12.91 |
| unsupported_x4_lora | wrong_statistic | 116 | 3.55 |
| unsupported_x4_lora | core_ok_but_full_wrong | 13 | 0.40 |
| unsupported_x4_lora | false_plot_unanswerable_as_answerable | 8 | 0.24 |

## Metadata LoRA Slice Breakdown

| run | slice | value | n | answerability_ok_pct | temporal_filter_ok_pct | core_intent_ok_pct | full_intent_ok_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| metadata_lora | domain | worldbank_expansion | 2943 | 85.19 | 93.00 | 84.51 | 84.47 |
| metadata_lora | domain | economy | 56 | 85.71 | 94.64 | 82.14 | 75.00 |
| metadata_lora | domain | environment | 54 | 85.19 | 92.59 | 85.19 | 85.19 |
| metadata_lora | domain | health | 54 | 85.19 | 96.30 | 85.19 | 85.19 |
| metadata_lora | domain | education | 27 | 85.19 | 96.30 | 81.48 | 81.48 |
| metadata_lora | domain | energy | 27 | 85.19 | 92.59 | 85.19 | 85.19 |
| metadata_lora | domain | finance | 27 | 85.19 | 92.59 | 81.48 | 81.48 |
| metadata_lora | domain | labor | 27 | 85.19 | 88.89 | 77.78 | 77.78 |
| metadata_lora | domain | population | 27 | 85.19 | 96.30 | 85.19 | 85.19 |
| metadata_lora | domain | technology | 27 | 85.19 | 92.59 | 81.48 | 81.48 |
| metadata_lora | gold_answerability | answerable | 2785 | 100.00 | 99.89 | 99.03 | 98.85 |
| metadata_lora | gold_answerability | unanswerable | 484 | 0.00 | 53.93 | 0.00 | 0.00 |
| metadata_lora | gold_temporal_filter_type | year_range | 1210 | 100.00 | 99.83 | 99.83 | 99.83 |
| metadata_lora | gold_temporal_filter_type | other | 1091 | 55.64 | 79.47 | 53.44 | 53.16 |
| metadata_lora | gold_temporal_filter_type | all_years | 484 | 100.00 | 100.00 | 100.00 | 99.79 |
| metadata_lora | gold_temporal_filter_type | latest_year | 484 | 100.00 | 100.00 | 99.79 | 99.59 |
| metadata_lora | language | en | 1937 | 87.51 | 99.43 | 86.37 | 86.22 |
| metadata_lora | language | vi | 1332 | 81.83 | 83.86 | 81.46 | 81.31 |
| metadata_lora | task_type | mixed_temporal_ranking | 242 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | stat_average_period | 242 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | stat_change | 242 | 100.00 | 100.00 | 99.59 | 98.76 |
| metadata_lora | task_type | stat_ranking_topk | 242 | 100.00 | 100.00 | 99.59 | 99.17 |
| metadata_lora | task_type | stat_unanswerable | 242 | 0.00 | 61.98 | 0.00 | 0.00 |
| metadata_lora | task_type | temporal_boundary_check | 242 | 100.00 | 99.17 | 99.17 | 99.17 |
| metadata_lora | task_type | temporal_granularity_unanswerable | 242 | 0.00 | 45.87 | 0.00 | 0.00 |
| metadata_lora | task_type | temporal_period_filter | 242 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_previous_window | 242 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_recent_window | 242 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_trend | 242 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | mixed_change_ranking | 121 | 100.00 | 100.00 | 86.78 | 86.78 |
| metadata_lora | task_type | mixed_temporal_distribution | 121 | 100.00 | 100.00 | 96.69 | 95.87 |
| metadata_lora | task_type | stat_distribution | 121 | 100.00 | 100.00 | 100.00 | 99.17 |
| metadata_lora | task_type | stat_outlier | 121 | 100.00 | 100.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_before_after | 121 | 100.00 | 99.17 | 99.17 | 99.17 |
| metadata_lora | temporal_coverage | medium_11_25 | 2052 | 85.19 | 92.64 | 84.75 | 84.70 |
| metadata_lora | temporal_coverage | very_long_>50 | 758 | 85.22 | 94.33 | 83.64 | 83.11 |
| metadata_lora | temporal_coverage | long_26_50 | 405 | 85.19 | 92.84 | 83.95 | 83.95 |
| metadata_lora | temporal_coverage | short_<=10 | 54 | 85.19 | 94.44 | 83.33 | 83.33 |

## Highest-Failure Groups

| run | group | value | n | full_failure_rate_pct | core_intent_ok_pct | temporal_filter_ok_pct |
| --- | --- | --- | --- | --- | --- | --- |
| metadata_lora | dataset_id | derived_gdp_structure_profile | 29 | 31.03 | 79.31 | 93.10 |
| metadata_lora | dataset_id | wb_asean_labor_force_participation | 27 | 22.22 | 77.78 | 88.89 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_co2_lu_ol_mt_ce_ar5_carbon_dioxide_co2_net_fluxes_from_lulucf_o | 27 | 22.22 | 81.48 | 88.89 |
| metadata_lora | dataset_id | wbexp_asean_enf_cont_durs_dy_dfrn_enforcing_contracts_time_days_score | 27 | 22.22 | 77.78 | 92.59 |
| metadata_lora | dataset_id | wb_asean_domestic_credit_private_sector | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wb_asean_fixed_broadband_subscriptions | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wb_asean_imports_share_gdp | 27 | 18.52 | 85.19 | 96.30 |
| metadata_lora | dataset_id | wb_asean_tertiary_school_enrollment | 27 | 18.52 | 81.48 | 96.30 |
| metadata_lora | dataset_id | wbexp_asean_bar_ter_icmp_6569_zs_barro_lee_percentage_of_population_age_65_69_with | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_bi_wag_totl_gd_zs_wage_bill_as_a_percentage_of_gdp | 27 | 18.52 | 81.48 | 88.89 |
| metadata_lora | dataset_id | wbexp_asean_bn_cab_xoka_gd_zs_current_account_balance_of_gdp | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_ef_efm_univ_xd_universal_economic_fitness_metric | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_eg_gdp_puse_ko_pp_kd_gdp_per_unit_of_energy_use_constant_2021_ppp_per_ | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_all_lu_mt_ce_ar5_total_greenhouse_gas_emissions_including_luluc | 27 | 18.52 | 81.48 | 88.89 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_ch4_mt_ce_ar5_methane_ch4_emissions_total_excluding_lulucf_mt_c | 27 | 18.52 | 81.48 | 88.89 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_ch4_pi_mt_ce_ar5_methane_ch4_emissions_from_power_industry_ener | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_co2_mt_ce_ar5_carbon_dioxide_co2_emissions_total_excluding_lulu | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_co2_rt_gdp_kd_carbon_intensity_of_gdp_kg_co2e_per_constant_2015 | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_fgas_ip_mt_ce_ar5_f_gases_emissions_from_industrial_processes_m | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | dataset_id | wbexp_asean_en_ghg_n2o_ag_mt_ce_ar5_nitrous_oxide_n2o_emissions_from_agriculture_m | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | domain | economy | 56 | 25.00 | 82.14 | 94.64 |
| metadata_lora | domain | labor | 27 | 22.22 | 77.78 | 88.89 |
| metadata_lora | domain | education | 27 | 18.52 | 81.48 | 96.30 |
| metadata_lora | domain | finance | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | domain | technology | 27 | 18.52 | 81.48 | 92.59 |
| metadata_lora | domain | worldbank_expansion | 2943 | 15.53 | 84.51 | 93.00 |
| metadata_lora | domain | environment | 54 | 14.81 | 85.19 | 92.59 |
| metadata_lora | domain | health | 54 | 14.81 | 85.19 | 96.30 |
| metadata_lora | domain | energy | 27 | 14.81 | 85.19 | 92.59 |
| metadata_lora | domain | population | 27 | 14.81 | 85.19 | 96.30 |
| metadata_lora | gold_temporal_filter_type | other | 1091 | 46.84 | 53.44 | 79.47 |
| metadata_lora | gold_temporal_filter_type | latest_year | 484 | 0.41 | 99.79 | 100.00 |
| metadata_lora | gold_temporal_filter_type | all_years | 484 | 0.21 | 100.00 | 100.00 |
| metadata_lora | gold_temporal_filter_type | year_range | 1210 | 0.17 | 99.83 | 99.83 |
| metadata_lora | task_type | stat_unanswerable | 242 | 100.00 | 0.00 | 61.98 |
| metadata_lora | task_type | temporal_granularity_unanswerable | 242 | 100.00 | 0.00 | 45.87 |
| metadata_lora | task_type | mixed_change_ranking | 121 | 13.22 | 86.78 | 100.00 |
| metadata_lora | task_type | mixed_temporal_distribution | 121 | 4.13 | 96.69 | 100.00 |
| metadata_lora | task_type | stat_change | 242 | 1.24 | 99.59 | 100.00 |
| metadata_lora | task_type | stat_ranking_topk | 242 | 0.83 | 99.59 | 100.00 |
| metadata_lora | task_type | temporal_boundary_check | 242 | 0.83 | 99.17 | 99.17 |
| metadata_lora | task_type | stat_distribution | 121 | 0.83 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_before_after | 121 | 0.83 | 99.17 | 99.17 |
| metadata_lora | task_type | mixed_temporal_ranking | 242 | 0.00 | 100.00 | 100.00 |
| metadata_lora | task_type | stat_average_period | 242 | 0.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_period_filter | 242 | 0.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_previous_window | 242 | 0.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_recent_window | 242 | 0.00 | 100.00 | 100.00 |
| metadata_lora | task_type | temporal_trend | 242 | 0.00 | 100.00 | 100.00 |
| metadata_lora | task_type | stat_outlier | 121 | 0.00 | 100.00 | 100.00 |
| qwen_prompt_only | dataset_id | derived_gdp_structure_profile | 29 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | owid_life_expectancy_vietnam | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_domestic_credit_private_sector | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_electricity_access | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_fertility_rate | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_fixed_broadband_subscriptions | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_forest_area_share | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_freshwater_withdrawal_share | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_hospital_beds | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_imports_share_gdp | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_labor_force_participation | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wb_asean_tertiary_school_enrollment | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_ag_lnd_agri_k2_agricultural_land_sq_km | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_ag_lnd_frst_k2_forest_area_sq_km | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_bar_noed_3034_fe_zs_barro_lee_percentage_of_female_population_age_30_3 | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_bar_noed_4044_zs_barro_lee_percentage_of_population_age_40_44_with_no_ | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_bar_noed_6064_zs_barro_lee_percentage_of_population_age_60_64_with_no_ | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_bar_noed_75up_fe_zs_barro_lee_percentage_of_female_population_age_75_w | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_bar_pop_1519_fe_barro_lee_population_in_thousands_age_15_19_female | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | dataset_id | wbexp_asean_bar_pop_2529_barro_lee_population_in_thousands_age_25_29_total | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | worldbank_expansion | 2943 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | economy | 56 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | environment | 54 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | health | 54 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | education | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | energy | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | finance | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | labor | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | population | 27 | 100.00 | 0.00 | 0.00 |
| qwen_prompt_only | domain | technology | 27 | 100.00 | 0.00 | 0.00 |

## Modeling Implications

- The metadata-aware LoRA remains the strongest current checkpoint on full-dev.
- Schema-only performance confirms that explicit temporal support metadata carries model-relevant information.
- Unsupported oversampling alone is not sufficient: it improves boundary behavior only weakly on full-dev and hurts temporal/core fidelity.
- The next method should target answerability as a calibrated gate and temporal-filter choice as a hard-negative ranking problem, not as SFT-only generation.
