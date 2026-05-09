# Architecture

## Design Principle

EV Flex Trading Ops Simulator should behave like a daily trading-support workflow, not a standalone price dashboard. The architecture is organized around a repeatable operational process:

1. Ingest market and fleet data.
2. Validate and normalize to half-hourly settlement periods.
3. Calculate fleet charging requirements.
4. Generate baseline and optimized schedules.
5. Aggregate depot load and calculate baseline charging cost.
6. Build scheduled positions from optimized charging.
7. Simulate actual metered charging scenarios.
8. Reconcile scheduled versus actual metered consumption.
9. Calculate simplified settlement-style exposure and P&L-style summaries.
10. Export Excel reporting and dashboard-ready reporting data.
11. Present the daily workflow in a local Streamlit dashboard.

The system should be modular enough to be credible to technical reviewers while staying lightweight enough to run locally with public or synthetic data.

## Target Package Layout

```text
src/ev_flex_trading/
  config.py
  ingestion/
    elexon_client.py
    neso_client.py
    epex_csv_loader.py
    sample_data_loader.py
  fleet/
    synthetic_fleet_generator.py
    fleet_requirements.py
    charging_profiles.py
  optimisation/
    charging_optimizer.py
    dumb_charging_baseline.py
    constraints.py
  trading/
    position_builder.py
    settlement_simulator.py
    pnl_report.py
    market_metrics.py
  reporting/
    excel_report.py
    dashboard_data.py
  dashboard/
    data_loader.py
  validation/
    data_quality_checks.py
    exceptions.py
  utils/
    settlement_periods.py
    timezones.py
    units.py
```

## Layers

### 1. Configuration and Paths

`config.py` should centralize project paths, default timezone assumptions, scenario names, and optional API configuration. It should avoid hidden environment assumptions and should never require secrets to run the sample workflow.

### 2. Ingestion

Ingestion modules should load raw market and operational data into normalized dataframes with explicit schemas.

Planned adapters:

- `elexon_client.py`: optional public ELEXON/BMRS data access for GB system or price data.
- `neso_client.py`: optional NESO public data access for system context.
- `epex_csv_loader.py`: sample CSV loader for EPEX-style day-ahead and intraday prices.
- `sample_data_loader.py`: helper for local sample inputs and generated fixtures.
- `synthetic_market_generator.py`: offline synthetic market prices for deterministic demos.
- `market_data_normalizer.py`: shared normalization into the market price schema.

Live public API access should be optional. Unit tests should use local fixtures.

### 3. Validation and Exceptions

Validation should produce structured exception records rather than only raising errors. The daily workflow should be able to continue where sensible while clearly flagging analyst review items.

Examples:

- missing price intervals
- duplicate timestamps
- impossible SoC values
- missing vehicle fields
- unassigned chargers
- negative meter readings
- stale input data
- violated operational constraints

Severe issues should fail the run when outputs would be misleading.

### 4. Settlement-Period Utilities

All market and operational series should be normalized to GB half-hourly settlement periods. Settlement-period logic should be centralized under `utils/settlement_periods.py`.

This layer should handle:

- timezone-aware timestamps
- local date filtering
- settlement period numbering
- period start and end timestamps
- daylight-saving edge cases where relevant

### 5. Fleet Requirements

Fleet modules should calculate vehicle-level charging demand and aggregate depot-level requirements.

Inputs include:

- arrival and departure windows
- start and target SoC
- battery capacity
- charger limits
- route priority
- assigned charger or depot constraints

Outputs should include required kWh, feasible charging windows, readiness status, and operational metrics.

### 6. Charging Schedules

The baseline scheduler models immediate charging subject to vehicle plug-in windows and charger limits. Phase 3 rounds arrivals up to the next half-hour and departures down to the previous half-hour, then charges each vehicle as soon as possible until the requirement is met or the window closes.

The optimizer should minimize cost against market prices subject to:

- vehicle availability
- target energy by departure
- charger max power
- site import capacity
- charging efficiency
- optional undercharge penalty for stressed or infeasible cases

Optimization should return both the schedule and diagnostics.

Phase 4 implements the optimizer as a linear program using SciPy `linprog`. Decision variables represent vehicle-interval charging energy, with optional unmet-energy slack variables carrying a high penalty. This allows stressed or constrained cases to produce structured undercharge diagnostics instead of unclear solver failures.

### 7. Baseline Costing and Comparison

Baseline costing joins depot-level immediate-charge load to normalized market prices by settlement date and settlement period. It calculates interval baseline charging cost, total delivered energy, weighted average charging price, peak import, and readiness metrics.

The optimization comparison layer calculates savings versus baseline, weighted average price improvement, peak import change, readiness, unmet energy, and materially shifted intervals.

This is not full trading P&L. It is the cost comparison case for later smart charging and settlement-style analysis.

### 8. Actuals and Reconciliation

Actual charging modules generate synthetic metered charging scenarios from the optimized schedule. Scenarios include base actuals, late arrivals, charger derating, missing meter data, and high deviation.

The reconciliation layer compares the scheduled position against actual metered charging by settlement period. It calculates deviation MWh, deviation percentage, missing actual intervals, material deviations, and structured exceptions for analyst review.

### 9. Trading and Settlement Simulation

Trading modules convert optimized schedules into a scheduled position and compare that position with actual metered demand.

Outputs should include:

- day-ahead forecast MWh
- intraday adjusted MWh
- scheduled/traded MWh
- actual metered MWh
- imbalance MWh
- imbalance/settlement-style cost
- dumb charging cost
- smart charging cost
- smart charging savings
- net daily cost/P&L versus baseline

Settlement-style exposure uses a simplified imbalance-price spread derived from market prices. It is not official settlement or real trading P&L.

### 10. Reporting

Reporting is a core product layer.

`excel_report.py` generates a professional workbook suitable for commercial analytics review. It uses `xlsxwriter` because the workbook is created from scratch and benefits from styled tables, formatting, charts, and worksheet-level layout control.

The dashboard layer reads generated CSV and Excel outputs without duplicating business logic. It prepares KPI, chart, scenario, and table inputs for the local Streamlit app.

`app/streamlit_app.py` consumes prepared outputs and stays focused on operational review: metrics, schedules, curves, exceptions, readiness, reconciliation, and links to the Excel workbook. Missing files are surfaced as user-facing warnings with regeneration guidance.

## Data Flow

```text
raw/sample/public data
        |
        v
ingestion adapters
        |
        v
validation + exception records
        |
        v
settlement-period normalization
        |
        v
fleet requirements + market prices
        |
        +--> dumb baseline schedule
        |          |
        |          v
        |    depot load + baseline charging cost
        |
        +--> optimized charging schedule
                   |
                   v
             optimized depot load + cost
                   |
                   v
             baseline-vs-optimized comparison
                   |
                   v
             scheduled position + actuals
                   |
                   v
             reconciliation + settlement-style exposure
                   |
                   v
             P&L-style daily summary
                   |
                   v
             Excel daily trading report
                   |
                   v
             Streamlit dashboard
        |
        v
position builder + actuals reconciliation
        |
        v
settlement/P&L-style metrics
        |
        +--> Excel report
        |
        +--> dashboard-ready outputs
```

## Storage

Early phases should use CSV and Parquet outputs under `data/` for simplicity. DuckDB or SQLite can be introduced later if it improves repeatability or dashboard performance.

Suggested folders:

- `data/raw/`: downloaded or original public data, when used.
- `data/sample_inputs/`: small committed sample datasets.
- `data/processed/`: normalized intermediate outputs.
- `data/outputs/`: generated reports and dashboard data.

Generated large outputs should not be committed unless intentionally included as small examples.

## CLI Boundary

The future CLI script `run_daily_trading_workflow.py` should orchestrate the workflow only. Business logic should live in package modules so it can be tested directly.

Target command:

```bash
python run_daily_trading_workflow.py --date 2026-05-09 --scenario base
```

## Scenario Design

Planned scenarios:

- `base`: normal fleet requirements and representative market prices.
- `price_spike`: high-price periods that reward flexibility.
- `late_vehicles`: delayed arrivals and compressed charging windows.
- `charger_outage`: reduced charger availability.
- `missing_data`: data-quality exceptions and analyst review workflow.
- `site_constrained`: depot import cap binds during peak charging demand.

Scenarios should be deterministic and documented.
