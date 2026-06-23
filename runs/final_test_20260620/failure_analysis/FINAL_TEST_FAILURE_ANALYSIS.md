# Paper 09 Final-Test Failure Analysis

This analysis is performed after the frozen one-time expanded-test run. It does not change the method.

## Policy Summary

| Metric | Value |
| --- | ---: |
| n | 3111 |
| Core-intent accuracy | 88.49% |
| Full-intent accuracy | 88.30% |
| Answerability accuracy | 99.10% |
| Temporal-filter accuracy | 93.73% |
| False-plot rate | 0.90% |
| Over-refusal rate | 0.00% |

## Dominant Policy Failure Types

| Failure type | Count | Rate |
| --- | ---: | ---: |
| wrong_task_type | 352 | 11.31% |
| wrong_temporal_filter | 195 | 6.27% |
| wrong_statistic | 38 | 1.22% |
| wrong_measure | 31 | 1.00% |
| false_plot | 28 | 0.90% |
| wrong_time_field | 28 | 0.90% |
| core_ok_but_full_wrong | 6 | 0.19% |

## Task-Type Policy Slices

| Task type | n | Full | Core | Temporal filter | Answerability |
| --- | ---: | ---: | ---: | ---: | ---: |
| mixed_change_ranking | 115 | 82.61% | 82.61% | 100.00% | 100.00% |
| mixed_temporal_distribution | 115 | 97.39% | 97.39% | 100.00% | 100.00% |
| mixed_temporal_ranking | 230 | 99.57% | 100.00% | 100.00% | 100.00% |
| stat_average_period | 230 | 100.00% | 100.00% | 100.00% | 100.00% |
| stat_change | 230 | 98.26% | 99.13% | 100.00% | 100.00% |
| stat_correlation_proxy | 6 | 0.00% | 0.00% | 83.33% | 100.00% |
| stat_distribution | 115 | 99.13% | 100.00% | 100.00% | 100.00% |
| stat_outlier | 115 | 100.00% | 100.00% | 100.00% | 100.00% |
| stat_ranking_topk | 230 | 97.39% | 98.26% | 100.00% | 100.00% |
| stat_unanswerable | 230 | 59.57% | 59.57% | 68.26% | 95.65% |
| temporal_before_after | 115 | 100.00% | 100.00% | 100.00% | 100.00% |
| temporal_boundary_check | 230 | 100.00% | 100.00% | 100.00% | 100.00% |
| temporal_granularity_unanswerable | 230 | 0.00% | 0.00% | 47.39% | 92.17% |
| temporal_period_filter | 230 | 100.00% | 100.00% | 100.00% | 100.00% |
| temporal_previous_window | 230 | 100.00% | 100.00% | 100.00% | 100.00% |
| temporal_recent_window | 230 | 100.00% | 100.00% | 100.00% | 100.00% |
| temporal_trend | 230 | 100.00% | 100.00% | 100.00% | 100.00% |

## Ranker Symmetric-Policy Sensitivity

| Task type | n | Symmetric correct | Fallback/order-sensitive |
| --- | ---: | ---: | ---: |
| mixed_change_ranking | 690 | 80.14% | 19.86% |
| temporal_recent_window | 1380 | 94.35% | 5.65% |
| stat_change | 1380 | 95.80% | 4.20% |
| temporal_previous_window | 1380 | 97.90% | 2.10% |
| stat_average_period | 1322 | 100.00% | 0.00% |
| temporal_boundary_check | 1376 | 100.00% | 0.00% |
| temporal_period_filter | 1322 | 100.00% | 0.00% |

## Representative Policy Failures

| Type | Sample | Task | Lang | Gold filter | Pred filter | Query |
| --- | --- | --- | --- | --- | --- | --- |
| full_only | paper09x_000387 | stat_change | en | 2015_to_2024 | 2015_to_2024 | Show the change in services share gdp from 2015 to 2024 by country. |
| task_type | paper09x_000393 | temporal_granularity_unanswerable | en | monthly | monthly | Show monthly services share gdp trends for Indonesia. |
| answerability | paper09x_000404 | temporal_granularity_unanswerable | vi | monthly | all_years | Ve xu huong hang thang cua services share gdp cho Indonesia. |
| task_type | paper09x_000405 | stat_unanswerable | vi | future | 2016_to_2024 | Du bao services share gdp nam sau theo thanh pho. |
| task_type | paper09x_000526 | mixed_change_ranking | en | 2014_to_2023 | 2014_to_2023 | Rank countries by growth in health expenditure pc over the last decade. |
| task_type | paper09x_000528 | temporal_granularity_unanswerable | en | monthly | monthly | Show monthly health expenditure pc trends for Philippines. |
| answerability | paper09x_000566 | temporal_granularity_unanswerable | vi | monthly | all_years | Ve xu huong hang thang cua health expenditure share gdp cho Malaysia. |
| answerability | paper09x_000755 | temporal_granularity_unanswerable | vi | monthly | all_years | Ve xu huong hang thang cua unemployment rate cho Malaysia. |
| answerability | paper09x_001403 | temporal_granularity_unanswerable | vi | monthly | all_years | Ve xu huong hang thang cua high technology exports share cho Vietnam. |
| temporal_filter | paper09x_001485 | stat_unanswerable | vi | future | all_years | Du bao gdp per capita nam sau theo thanh pho. |
| full_only | paper09x_001522 | stat_ranking_topk | en | latest_year | latest_year | Rank the top 5 countries by latest population. |
| full_only | paper09x_001523 | stat_distribution | en | all_years | all_years | Show the distribution of population across countries and years. |
