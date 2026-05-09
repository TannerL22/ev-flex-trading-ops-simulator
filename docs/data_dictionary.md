# Data Dictionary

This document defines the expected schemas for the main project datasets. Field names may evolve during implementation, but changes should preserve the same business meaning and update this file.

## Common Conventions

- Timestamps should be timezone-aware where possible.
- GB local trading days should be handled explicitly.
- Energy values should use `kWh` for vehicle-level fields and `MWh` for market/trading aggregates where practical.
- Power values should use `kW` for charger/vehicle-level fields and `MW` for site or market-level aggregates.
- Prices should use `GBP/MWh`.
- Settlement-period data should include both `settlement_date` and `settlement_period`.

## Market Prices

Purpose: normalized half-hourly market price data used for scheduling, reporting, and settlement-style calculations.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| timestamp | datetime | n/a | Timezone-aware period start timestamp in Europe/London where practical. |
| settlement_date | date | n/a | GB local settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period number for the local date. Normal days have 48 periods; clock-change days may have 46 or 50. |
| price_gbp_per_mwh | float | GBP/MWh | Market or system price. Negative prices are allowed. |
| source | string | n/a | Source identifier such as `synthetic`, `sample_epex_csv`, or `elexon_insights`. |
| market | string | n/a | Market or source category such as `day_ahead`, `intraday`, `system_price`, or `synthetic_day_ahead`. |
| price_type | string | n/a | Price type such as `auction_clearing`, `system_buy`, `system_sell`, `mid`, or `synthetic`. |
| currency | string | n/a | Expected to be `GBP` for normalized data. |
| unit | string | n/a | Expected to be `MWh` for normalized data. |
| ingestion_timestamp | datetime | n/a | Time the row was loaded or generated. |
| data_quality_flag | string | n/a | Flag such as `ok` or `review`. |
| notes | string | n/a | Optional source or scenario note. |

Market validation checks include missing columns, null timestamps, non-numeric prices, duplicate settlement periods, missing intervals, invalid periods, implausible price magnitudes above 1000 GBP/MWh, mixed currencies, and mixed units.

## Fleet Schedule

Purpose: forecast or planned vehicle charging requirement data before optimization.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| service_date | date | n/a | Date the vehicle requirement belongs to. |
| depot_id | string | n/a | Depot or site identifier. |
| vehicle_id | string | n/a | Vehicle identifier. |
| vehicle_type | string | n/a | Vehicle class, such as `single_deck_bus`, `double_deck_bus`, or `commercial_van`. |
| arrival_time | datetime | n/a | Expected plug-in or depot arrival timestamp. |
| departure_time | datetime | n/a | Required departure timestamp. |
| battery_kwh | float | kWh | Vehicle battery capacity. |
| start_soc_pct | float | percent | Expected state of charge at arrival. |
| target_soc_pct | float | percent | Required state of charge by departure. |
| max_charger_kw | float | kW | Maximum charging power available to the vehicle. |
| assigned_charger_id | string | n/a | Charger identifier if assigned before scheduling. |
| priority | string | n/a | Operational priority such as `high`, `normal`, or `low`. |
| route_block | string | n/a | Route or duty block identifier. |

## Fleet Requirements

Purpose: calculated vehicle-level energy requirement and basic feasibility output.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| required_kwh | float | kWh | `battery_kwh * (target_soc_pct - start_soc_pct) / 100`, clipped at zero. |
| available_charging_hours | float | hours | Time between arrival and departure. |
| min_average_kw_required | float | kW | Average charging power needed across the plug-in window. |
| feasibility_flag | string | n/a | `feasible`, `infeasible`, or `no_energy_required`. |
| feasibility_message | string | n/a | Analyst-readable feasibility explanation. |

## Actual Charging

Purpose: metered or simulated actual charging data used for reconciliation.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| vehicle_id | string | n/a | Vehicle identifier where available. |
| assigned_charger_id | string | n/a | Assigned charger identifier. |
| timestamp | datetime | n/a | Interval timestamp or period start. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| scheduled_charge_kwh | float | kWh | Scheduled vehicle charging energy. |
| actual_charge_kwh | float | kWh | Synthetic actual metered charging energy. |
| actual_charge_kw | float | kW | Synthetic actual average charging power. |
| meter_quality_flag | string | n/a | `ok`, `missing`, or review flag. |
| actuals_scenario | string | n/a | Scenario such as `base_actuals` or `high_deviation`. |
| disruption_type | string | n/a | Synthetic disruption type. |
| notes | string | n/a | Analyst-readable note. |

## Optimized Schedule

Purpose: vehicle-level or charger-level optimized charging schedule by settlement period. This is planned for a later phase.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| service_date | date | n/a | Date of the schedule. |
| depot_id | string | n/a | Depot or site identifier. |
| vehicle_id | string | n/a | Vehicle identifier. |
| charger_id | string | n/a | Charger identifier. |
| settlement_date | date | n/a | GB local settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| scheduled_energy_kwh | float | kWh | Scheduled charging energy in the interval. |
| scheduled_power_kw | float | kW | Scheduled average charging power. |
| price_gbp_per_mwh | float | GBP/MWh | Price used by optimization. |
| marginal_cost_gbp | float | GBP | Interval charging cost. |
| schedule_type | string | n/a | `optimized`, `dumb_baseline`, or scenario label. |
| constraint_flag | string | n/a | Optional flag such as `site_cap_binding`, `charger_limit`, or `vehicle_window`. |

## Baseline Vehicle Schedule

Purpose: vehicle-level half-hourly schedule for the non-optimized immediate-charge baseline.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| vehicle_id | string | n/a | Vehicle identifier. |
| assigned_charger_id | string | n/a | Assigned charger identifier from fleet schedule. |
| timestamp | datetime | n/a | Half-hour interval start. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| interval_hours | float | hours | Interval duration, normally `0.5`. |
| charge_kw | float | kW | Average charging power used by the vehicle in the interval. |
| charge_kwh | float | kWh | Energy delivered in the interval. |
| cumulative_charge_kwh | float | kWh | Cumulative delivered energy for the vehicle. |
| required_kwh | float | kWh | Vehicle charging requirement. |
| remaining_kwh_after_interval | float | kWh | Remaining requirement after the interval. |
| baseline_strategy | string | n/a | `immediate_charge`. |
| feasibility_flag | string | n/a | `feasible`, `in_progress`, `infeasible`, or `no_energy_required`. |
| notes | string | n/a | Analyst-readable note. |

## Baseline Depot Load

Purpose: depot-level aggregate load from the immediate-charge vehicle baseline.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| timestamp | datetime | n/a | Half-hour interval start. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| depot_id | string | n/a | Depot or site identifier. |
| total_charge_kwh | float | kWh | Total depot charging energy in the interval. |
| total_charge_mwh | float | MWh | Total depot charging energy in MWh. |
| average_charge_kw | float | kW | Average depot charging power in the interval. |
| interval_kw | float | kW | `total_charge_kwh / 0.5`. |
| active_vehicle_count | integer | count | Number of vehicles charging in the interval. |
| charger_count_used | integer | count | Number of assigned chargers active in the interval. |

## Baseline Cost By Interval

Purpose: interval-level baseline charging cost after joining depot load to normalized market prices.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| timestamp | datetime | n/a | Half-hour interval start. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| depot_id | string | n/a | Depot or site identifier. |
| total_charge_mwh | float | MWh | Depot charging energy in the interval. |
| price_gbp_per_mwh | float | GBP/MWh | Joined market price. |
| interval_cost_gbp | float | GBP | `total_charge_mwh * price_gbp_per_mwh`. |
| market | string | n/a | Market/source category used for costing. |
| source | string | n/a | Price source identifier. |
| price_type | string | n/a | Price type used for costing. |
| data_quality_flag | string | n/a | Market price quality flag. |

## Baseline Summary

Purpose: one-row summary of the dumb-charging baseline and baseline charging cost. This is not full trading P&L.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Service date covered by the baseline. |
| depot_id | string | n/a | Depot or site identifier. |
| total_required_mwh | float | MWh | Total vehicle charging requirement included in the schedule. |
| total_delivered_mwh | float | MWh | Total delivered baseline charging energy. |
| total_baseline_cost_gbp | float | GBP | Total immediate-charge baseline cost. |
| weighted_avg_price_gbp_per_mwh | float | GBP/MWh | Energy-weighted average charging price. |
| peak_import_kw | float | kW | Maximum depot interval import in the baseline. |
| vehicles_total | integer | count | Vehicles included in the baseline schedule. |
| vehicles_fully_charged | integer | count | Vehicles with no remaining requirement in the baseline. |
| vehicles_undercharged | integer | count | Vehicles not fully charged in the baseline. |
| vehicle_readiness_pct | float | percent | `vehicles_fully_charged / vehicles_total * 100`. |
| missing_price_intervals | integer | count | Charging intervals without a joined market price. |
| exception_count | integer | count | Structured exceptions raised during baseline costing. |
| notes | string | n/a | Summary note and limitations. |

## Optimized Vehicle Schedule

Purpose: vehicle-level half-hourly schedule produced by the smart charging optimizer.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| vehicle_id | string | n/a | Vehicle identifier. |
| assigned_charger_id | string | n/a | Assigned charger identifier from fleet schedule. |
| timestamp | datetime | n/a | Half-hour interval start. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| interval_hours | float | hours | Interval duration, normally `0.5`. |
| charge_kw | float | kW | Average charging power used by the vehicle in the interval. |
| charge_kwh | float | kWh | Energy delivered in the interval. |
| cumulative_charge_kwh | float | kWh | Cumulative delivered energy for the vehicle. |
| required_kwh | float | kWh | Vehicle charging requirement. |
| remaining_kwh_after_interval | float | kWh | Remaining requirement after the interval. |
| optimized_strategy | string | n/a | `price_optimized`. |
| price_gbp_per_mwh | float | GBP/MWh | Market price used by the optimizer. |
| market | string | n/a | Market/source category used for optimization. |
| source | string | n/a | Price source identifier. |
| price_type | string | n/a | Price type used for optimization. |
| data_quality_flag | string | n/a | Market price quality flag. |
| interval_cost_gbp | float | GBP | `charge_kwh / 1000 * price_gbp_per_mwh`. |
| feasibility_flag | string | n/a | `feasible` or `undercharged`. |
| unmet_kwh | float | kWh | Vehicle unmet energy from optimizer slack variable. |
| notes | string | n/a | Analyst-readable note. |

## Optimized Depot Load

Purpose: depot-level aggregate load from the optimized schedule.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| timestamp | datetime | n/a | Half-hour interval start. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| depot_id | string | n/a | Depot or site identifier. |
| total_charge_kwh | float | kWh | Total optimized depot charging energy in the interval. |
| total_charge_mwh | float | MWh | Total optimized depot charging energy in MWh. |
| interval_kw | float | kW | `total_charge_kwh / 0.5`. |
| active_vehicle_count | integer | count | Number of vehicles charging in the interval. |
| charger_count_used | integer | count | Number of assigned chargers active in the interval. |
| site_import_limit_kw | float | kW | Optional site import cap used by optimizer. |
| import_limit_utilization_pct | float | percent | Utilization of site import cap where provided. |
| price_gbp_per_mwh | float | GBP/MWh | Market price for interval. |
| interval_cost_gbp | float | GBP | Optimized interval charging cost. |

## Optimization Summary

Purpose: one-row comparison of optimized charging versus the dumb baseline.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Service date covered by the run. |
| depot_id | string | n/a | Depot or site identifier. |
| vehicles_total | integer | count | Vehicles included in optimization. |
| vehicles_fully_charged | integer | count | Vehicles with no unmet energy. |
| vehicles_undercharged | integer | count | Vehicles with unmet energy. |
| vehicle_readiness_pct | float | percent | Vehicles fully charged divided by total vehicles. |
| total_required_mwh | float | MWh | Total required energy. |
| optimized_delivered_mwh | float | MWh | Energy delivered by optimized schedule. |
| optimized_cost_gbp | float | GBP | Optimized charging cost. |
| optimized_weighted_avg_price_gbp_per_mwh | float | GBP/MWh | Optimized weighted average charging price. |
| optimized_peak_import_kw | float | kW | Optimized peak depot import. |
| baseline_delivered_mwh | float | MWh | Energy delivered by immediate-charge baseline. |
| baseline_cost_gbp | float | GBP | Baseline charging cost. |
| baseline_weighted_avg_price_gbp_per_mwh | float | GBP/MWh | Baseline weighted average charging price. |
| baseline_peak_import_kw | float | kW | Baseline peak depot import. |
| savings_gbp | float | GBP | Baseline cost minus optimized cost. |
| savings_pct | float | percent | Savings as percentage of baseline cost. |
| peak_reduction_kw | float | kW | Baseline peak minus optimized peak. Negative values mean optimization increased peak import. |
| peak_reduction_pct | float | percent | Peak reduction as percentage of baseline peak. |
| total_unmet_mwh | float | MWh | Total unmet optimized energy. |
| site_import_limit_kw | float | kW | Optional site import cap used. |
| exception_count | integer | count | Structured exceptions raised. |
| materially_shifted_intervals | integer | count | Intervals where optimized load differs materially from baseline. |
| notes | string | n/a | Summary note and limitations. |

Example optimization exceptions:

- `Vehicle has unmet energy after optimization.`
- `Missing market price for valid optimization interval.`
- `Optimizer failed: ...`
- `Vehicle has no valid charging windows for optimization.`

## Scheduled Position

Purpose: half-hourly scheduled energy position derived from optimized charging.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| timestamp | datetime | n/a | Interval timestamp. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| scheduled_mwh | float | MWh | Scheduled energy position. |
| scheduled_kw | float | kW | Scheduled average power. |
| market | string | n/a | Market/source category used for scheduled prices. |
| source | string | n/a | Price source identifier. |
| position_type | string | n/a | `optimized_schedule` or `site_cap_optimized_schedule`. |
| notes | string | n/a | Analyst-readable note. |

## Reconciliation

Purpose: interval-level scheduled-vs-actual comparison.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| timestamp | datetime | n/a | Interval timestamp. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| scheduled_mwh | float | MWh | Scheduled energy. |
| actual_mwh | float | MWh | Actual metered energy, null when meter data is missing. |
| deviation_mwh | float | MWh | Actual minus scheduled energy. |
| deviation_pct | float | percent | Deviation divided by scheduled energy. |
| abs_deviation_mwh | float | MWh | Absolute deviation. |
| scheduled_kw | float | kW | Scheduled average power. |
| actual_kw | float | kW | Actual average power. |
| meter_quality_flag | string | n/a | Meter quality flag. |
| reconciliation_status | string | n/a | `matched`, `minor_deviation`, `material_deviation`, `missing_actual`, `missing_schedule`, or `invalid_actual`. |
| exception_flag | boolean | n/a | Whether the interval should be reviewed. |
| notes | string | n/a | Analyst-readable note. |

## Settlement-Style Exposure

Purpose: simplified interval-level exposure calculation from scheduled-vs-actual deviations. This is not official settlement.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| timestamp | datetime | n/a | Interval timestamp. |
| settlement_date | date | n/a | GB settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| scheduled_mwh | float | MWh | Scheduled energy. |
| actual_mwh | float | MWh | Actual metered energy. |
| deviation_mwh | float | MWh | Actual minus scheduled energy. |
| scheduled_price_gbp_per_mwh | float | GBP/MWh | Reference scheduled price. |
| imbalance_price_gbp_per_mwh | float | GBP/MWh | Synthetic imbalance-style price. |
| scheduled_cost_gbp | float | GBP | Scheduled energy cost. |
| actual_energy_cost_gbp | float | GBP | Actual energy at scheduled price, included as an analytical reference. |
| imbalance_spread_cost_gbp | float | GBP | Deviation volume multiplied by the difference between imbalance price and scheduled price. |
| imbalance_exposure_gbp | float | GBP | Deviation volume priced at the simplified imbalance price. |
| total_settlement_style_cost_gbp | float | GBP | Scheduled position cost plus deviation volume priced at the simplified imbalance price. |
| pricing_method | string | n/a | Pricing method used. |
| notes | string | n/a | Limitation note. |

## P&L-Style Daily Summary

Purpose: one-row daily trading-support summary. This is not real trading P&L.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| service_date | date | n/a | Fleet service date. |
| depot_id | string | n/a | Depot or site identifier. |
| scenario | string | n/a | Actuals scenario. |
| vehicles_total | integer | count | Vehicle count. |
| scheduled_mwh | float | MWh | Total scheduled energy. |
| actual_mwh | float | MWh | Total actual metered energy. |
| deviation_mwh | float | MWh | Total actual minus scheduled energy. |
| absolute_deviation_mwh | float | MWh | Sum of absolute interval deviations. |
| deviation_pct | float | percent | Total deviation divided by scheduled energy. |
| scheduled_cost_gbp | float | GBP | Scheduled cost. |
| actual_energy_cost_gbp | float | GBP | Actual energy at scheduled price, included as an analytical reference. |
| imbalance_exposure_gbp | float | GBP | Total deviation volume priced at the simplified imbalance price. |
| total_settlement_style_cost_gbp | float | GBP | Scheduled position cost plus deviation volume priced at the simplified imbalance price. |
| dumb_baseline_cost_gbp | float | GBP | Dumb baseline cost. |
| optimized_expected_cost_gbp | float | GBP | Expected optimized cost. |
| expected_savings_vs_baseline_gbp | float | GBP | Baseline cost minus expected optimized cost. |
| realized_savings_vs_baseline_gbp | float | GBP | Baseline cost minus settlement-style cost. |
| realized_savings_vs_baseline_pct | float | percent | Realized savings percentage. |
| delta_vs_optimized_plan_gbp | float | GBP | Settlement-style cost minus expected optimized cost. |
| vehicle_readiness_pct | float | percent | Planned optimized readiness percentage. |
| material_deviation_intervals | integer | count | Material deviation interval count. |
| missing_meter_intervals | integer | count | Missing actual interval count. |
| exception_count | integer | count | Structured exception count. |
| notes | string | n/a | Limitation note. |

## Market Participation Metrics

Purpose: compact trading-support metrics for daily reports.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| total_scheduled_mwh | float | MWh | Total scheduled energy. |
| total_actual_mwh | float | MWh | Total actual energy. |
| active_settlement_periods | integer | count | Periods with scheduled energy. |
| average_scheduled_mw | float | MW | Average scheduled MW across active periods. |
| peak_scheduled_mw | float | MW | Peak scheduled MW. |
| peak_actual_mw | float | MW | Peak actual MW. |
| mean_absolute_deviation_mwh | float | MWh | Average absolute interval deviation. |
| mean_absolute_percentage_deviation | float | percent | Average absolute percentage deviation. |
| material_deviation_interval_count | integer | count | Count of material deviation intervals. |
| missing_actual_interval_count | integer | count | Count of missing actual intervals. |
| intervals_with_negative_prices | integer | count | Count of intervals with negative prices. |
| intervals_with_positive_deviation | integer | count | Actual greater than scheduled. |
| intervals_with_negative_deviation | integer | count | Actual less than scheduled. |

## Excel Workbook

Purpose: stakeholder-ready daily trading support report generated from Phase 1-5 outputs.

Workbook path:

```text
data/outputs/ev_flex_daily_trading_report_sample.xlsx
```

Sheets:

| Sheet | Purpose |
| --- | --- |
| README | Workbook purpose, report date, run ID, generated timestamp, limitations, and sheet descriptions. |
| Daily Summary | Executive KPI view, base/high-deviation scenario summaries, and cost comparison chart. |
| Baseline vs Optimized | Immediate-charge baseline versus site-cap optimized charging, including load profile comparison. |
| Scheduled vs Actual | Base actuals scheduled-vs-actual reconciliation and status summary. |
| Settlement Exposure | Simplified settlement-style exposure, not official settlement. |
| Market Metrics | Trading-support participation and deviation metrics. |
| Exceptions | Analyst review queue with severity formatting. |
| Fleet Requirements | Synthetic fleet requirements and feasibility data. |
| Market Prices | Normalized synthetic/sample market prices. |
| Baseline Schedule | Immediate-charge vehicle-level schedule. |
| Optimized Schedule | Price-optimized vehicle-level schedule. |
| Actual Charging | Synthetic actual metered charging data. |
| Assumptions | Model assumptions, units, and limitations. |

## Dashboard Inputs

Purpose: local Streamlit presentation layer over generated Phase 1-6 outputs.

| Dashboard Section | Primary Inputs | Description |
| --- | --- | --- |
| Overview | `phase5_daily_summary_*`, `phase5_market_participation_metrics_sample.csv` | Headline daily KPIs and scenario comparison. |
| Fleet & Market Inputs | `fleet_requirements_sample.csv`, `market_prices_synthetic_base.csv` | Fleet energy requirements and market price curve. |
| Baseline vs Optimized | `baseline_depot_load_sample.csv`, `optimized_depot_load_site_cap_sample.csv`, `phase4_optimization_summary_site_cap_sample.csv` | Immediate-charge baseline versus site-cap optimized charging. |
| Scheduled vs Actual | `reconciliation_*`, `actual_charging_*` | Reconciliation status, scheduled MWh, actual MWh, and deviation MWh. |
| Settlement Exposure | `settlement_style_exposure_*` | Simplified settlement-style exposure by settlement period. |
| Exceptions | `phase5_reconciliation_exceptions_sample.csv` | Analyst-review queue by severity and category. |
| Data Tables / Downloads | Generated CSV outputs and Excel workbook | Data previews and local downloads for report artifacts. |
| Methodology & Limitations | Static app text | Public-safe explanation of assumptions and limitations. |

## P&L / Settlement Output

Purpose: period-level and daily trading-support metrics comparing schedule, actuals, and baseline. This is planned for a later phase.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| service_date | date | n/a | Trading or service date. |
| settlement_date | date | n/a | GB local settlement date. |
| settlement_period | integer | n/a | Half-hourly settlement period. |
| forecast_mwh | float | MWh | Day-ahead or expected charging demand. |
| intraday_adjusted_mwh | float | MWh | Updated forecast if available. |
| scheduled_mwh | float | MWh | Scheduled or simulated traded energy position. |
| actual_mwh | float | MWh | Actual metered charging energy. |
| imbalance_mwh | float | MWh | Actual minus scheduled energy. |
| market_price_gbp_per_mwh | float | GBP/MWh | Scheduling or reference market price. |
| imbalance_price_gbp_per_mwh | float | GBP/MWh | Simplified imbalance or settlement-style price assumption. |
| dumb_cost_gbp | float | GBP | Baseline charging cost. |
| smart_cost_gbp | float | GBP | Optimized schedule cost. |
| imbalance_cost_gbp | float | GBP | Settlement-style cost from imbalance. |
| net_cost_gbp | float | GBP | Smart cost plus imbalance cost, subject to documented assumptions. |
| savings_vs_baseline_gbp | float | GBP | Dumb baseline cost minus net optimized cost. |
| participation_flag | string | n/a | Optional flag for periods with scheduled market participation. |

## Exceptions

Purpose: structured analyst-review log for data quality, operational, and calculation issues.

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| run_id | string | n/a | Workflow run identifier. |
| timestamp | datetime | n/a | Time the exception was detected or associated event time. |
| severity | string | n/a | `low`, `medium`, `high`, or `critical`. |
| category | string | n/a | `market_data`, `fleet_data`, `meter_data`, `optimization`, `settlement`, or `reporting`. |
| entity_id | string | n/a | Related vehicle, charger, depot, file, or settlement period identifier. |
| message | string | n/a | Human-readable explanation for analyst review. |
| suggested_action | string | n/a | Suggested next step. |

Example market-data exceptions:

- `Missing half-hourly market interval.`
- `Duplicate market price record for settlement period, market, and source.`
- `Market price is missing or non-numeric.`
- `Implausible market price magnitude above 1000 GBP/MWh.`
- `Mixed currencies detected in market price data.`

## Daily Summary Metrics

Purpose: top-level metrics for Excel and dashboard summary views in later phases.

| Metric | Unit | Description |
| --- | --- | --- |
| total_vehicles | count | Vehicles included in the trading day. |
| vehicles_ready_by_departure | count | Vehicles meeting target SoC by departure. |
| vehicles_undercharged | count | Vehicles below target at departure. |
| average_start_soc_pct | percent | Average start state of charge. |
| average_target_soc_pct | percent | Average target state of charge. |
| total_required_mwh | MWh | Total forecast charging requirement. |
| actual_metered_mwh | MWh | Total actual metered charging. |
| site_peak_import_mw | MW | Maximum scheduled or actual site import. |
| charger_utilization_pct | percent | Average charger utilization. |
| missed_readiness_events | count | Count of missed readiness cases. |
| weighted_average_charging_price_gbp_per_mwh | GBP/MWh | Energy-weighted optimized charging price. |
| dumb_charging_cost_gbp | GBP | Baseline cost. |
| smart_charging_cost_gbp | GBP | Optimized schedule cost. |
| smart_charging_savings_gbp | GBP | Smart cost saving versus dumb baseline before imbalance assumptions. |
| imbalance_mwh | MWh | Total absolute or net imbalance, as documented. |
| imbalance_cost_gbp | GBP | Simplified settlement-style imbalance cost. |
| net_daily_cost_gbp | GBP | Net simulated daily cost. |
| exceptions_count | count | Total exceptions raised. |
| high_severity_exceptions_count | count | Exceptions requiring urgent review. |
