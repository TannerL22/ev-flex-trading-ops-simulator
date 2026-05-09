# Execution Plan

## Phase 0: Planning and Scaffold

Status: complete

Goals:

- Define project positioning and role alignment.
- Create durable instructions for future Codex sessions.
- Document target architecture and data contracts.
- Create empty repo structure without implementing core application logic.

Deliverables:

- `PROJECT_BRIEF.md`
- `AGENTS.md`
- `EXECUTION_PLAN.md`
- `README.md`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- Minimal folder scaffold

## Phase 1: Repo Setup, Data Model, Synthetic Data, Settlement Periods

Status: complete

Goals:

- Initialize Python packaging and dependency management.
- Define core configuration and path handling.
- Implement settlement-period utilities for GB half-hourly periods.
- Create reproducible synthetic EV fleet schedule generator.
- Add initial data validation patterns and fixtures.

Key outputs:

- `pyproject.toml`
- package skeleton under `src/ev_flex_trading/`
- deterministic sample input CSVs
- tests for settlement periods and synthetic data generation
- Phase 1 sample generation script

Acceptance criteria:

- `pytest` runs locally.
- A fixed seed produces stable sample fleet data.
- Settlement-period mapping handles timezone-aware timestamps correctly.
- Generated sample fleet requirements and exception outputs are written locally.

## Phase 2: Market Data Ingestion and Adapters

Status: complete

Goals:

- Implement sample EPEX-style CSV loader.
- Design ELEXON/BMRS public API client for relevant GB price or system data.
- Optionally add NESO public data adapter for system context.
- Normalize all market data to a common half-hourly schema.
- Add validation for missing intervals, duplicates, units, and bad timestamps.

Key outputs:

- market-price schema
- public-data adapter interfaces
- sample EPEX day-ahead and intraday CSVs
- tests using local fixtures, not live API calls

Acceptance criteria:

- Sample CSVs can be loaded and normalized.
- Market data quality checks produce structured exceptions.
- Live API access is optional and not required to run the project.
- Tests use mocked API responses and local sample data only.

## Phase 3: Fleet Requirements and Dumb Charging Baseline

Status: complete

Goals:

- Calculate required energy from arrival/departure windows, battery capacity, start SoC, and target SoC.
- Normalize fleet requirements to settlement periods.
- Build a dumb charging baseline that charges immediately on arrival subject to charger limits.
- Compute operational metrics such as total MWh, readiness, peak import, and charger utilization.

Key outputs:

- fleet requirement tables
- dumb baseline schedule
- initial fleet metrics
- tests for requirements and baseline scheduling

Acceptance criteria:

- Vehicles charge only while plugged in.
- Baseline respects charger max power and basic vehicle constraints.
- Undercharged or infeasible vehicles are clearly flagged.
- Depot load and baseline charging cost outputs are generated from sample data.

## Phase 4: Optimization Engine

Status: complete

Goals:

- Implement price-responsive charging optimization.
- Minimize charging cost subject to vehicle readiness, plug-in windows, charger max power, site import capacity, and optional efficiency.
- Add scenario support for site constraints, price spikes, late arrivals, and charger outages.
- Provide meaningful infeasibility diagnostics.

Key outputs:

- optimized schedule table
- optimizer assumptions
- constraint and feasibility checks
- tests for cost ordering, readiness, and constraint satisfaction

Acceptance criteria:

- Optimized charging is no more expensive than dumb charging in normal unconstrained cases.
- Constraints are explicit and test-covered.
- Infeasible cases produce exceptions rather than silent bad outputs.
- Optional site import cap scenario is generated for demonstration.

## Phase 5: Trading Position, Forecast-vs-Actual, Settlement/P&L Simulation

Status: complete

Goals:

- Convert forecast and optimized schedule into a scheduled/traded position.
- Reconcile day-ahead forecast, intraday adjusted forecast, scheduled energy, and actual metered energy.
- Calculate imbalance volume by settlement period.
- Estimate simplified settlement-style exposure using available price data or documented assumptions.
- Calculate P&L-style cost versus dumb baseline.
- Produce market participation metrics.

Key outputs:

- position table
- forecast-vs-actual table
- P&L and settlement exposure table
- market participation metrics
- tests for settlement and reconciliation calculations

Acceptance criteria:

- Metrics reconcile to source schedules and actuals.
- Assumptions are documented.
- Outputs avoid overstating real trading functionality.
- Base and high-deviation actuals scenarios produce daily summaries and exception logs.

## Phase 6: Excel Report

Goals:

- Generate a professional daily trading workbook.
- Make Excel output central to the project value proposition.
- Include clear summary, source data tabs, schedules, reconciliation, P&L-style outputs, exceptions, and assumptions.

Workbook tabs:

- Daily Summary
- Market Prices
- Fleet Requirements
- Optimised Schedule
- Dumb Charging Baseline
- Forecast vs Actual
- P&L / Settlement Exposure
- Exceptions Log
- Assumptions

Acceptance criteria:

- Workbook opens cleanly in Excel.
- Tabs are readable and formatted.
- Key metrics are visible without requiring code review.
- Exceptions are easy for an analyst to review.

## Phase 7: Streamlit Dashboard

Goals:

- Build a lightweight operational dashboard.
- Present price curves, charging schedules, cost comparison, forecast-vs-actual, readiness, settlement exposure, and exceptions.
- Keep the dashboard utilitarian and decision-focused.

Key views:

- Daily overview
- Price and schedule
- Fleet readiness
- Forecast-vs-actual
- P&L / settlement exposure
- Exceptions requiring review

Acceptance criteria:

- Dashboard runs locally from generated output data.
- It supports quick analyst review of the trading day.
- It avoids marketing-page styling and focuses on operational use.

## Phase 8: Tests, Polish, Screenshots, README, Application Brief

Goals:

- Strengthen tests and documentation.
- Add screenshots of Excel and dashboard outputs.
- Finalize README with setup, usage, architecture, assumptions, and AI-assisted development note.
- Create a one-page application brief and optional two-minute demo script.

Key outputs:

- polished README
- `docs/user_guide.md`
- `docs/market_context.md`
- `docs/application_brief.md`
- `docs/demo_script.md`
- screenshots
- test coverage for core workflows

Acceptance criteria:

- A reviewer can clone the repo, run the sample workflow, view outputs, and understand the project in under 10 minutes.
- The project is technically credible and commercially clear.
