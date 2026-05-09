# Repo Instructions for Codex Sessions

## Project Intent

This repository is a public-facing portfolio project for EV flexibility trading analytics. It should read as a polished independent showcase of data processing, half-hourly settlement logic, forecast-vs-actual reconciliation, Python automation, Excel reporting, and operational analytics.

Do not describe it as a production trading platform, financial advice, a real market-participation system, or anything affiliated with any company. Do not imply the project uses proprietary data, internal systems, private processes, or employer-specific knowledge.

## Public Repo Hygiene

- Keep public docs professional and recruiter/hiring-manager friendly.
- Do not include private job-search strategy, resume notes, employer-private details, colleague names, transaction context, lender names, or internal project names.
- Use public market concepts only, such as GB settlement periods, ELEXON/BMRS, EPEX-style CSVs, NESO public data, price-responsive charging, and imbalance-style exposure.
- Use public, synthetic, or sample data only.
- Keep assumptions visible and avoid overstating realism.
- Add private scratch material only under `private_notes/`; that folder must remain gitignored.

## Data and Secrets

- Do not commit secrets, API keys, credentials, cookies, tokens, paid data, or proprietary data.
- `.env.example` may document optional public configuration only.
- Live public APIs must be optional; sample workflows should run without network access.
- Unit tests must not depend on live APIs.

## Coding Standards

- Target Python 3.11+.
- Prefer simple, typed, modular Python.
- Keep business logic out of scripts where practical; scripts should orchestrate package functions.
- Use pandas/numpy for tabular workflow logic.
- Keep timezone and settlement-period logic centralized.
- Avoid hardcoded absolute paths; use `pathlib` and project config helpers.
- Add comments only where they clarify non-obvious business rules or date/time assumptions.

## Validation Standards

- Data quality checks should return structured exceptions, not only printed warnings.
- Severe data issues may raise errors when continuing would create misleading outputs.
- Reusable schemas should define expected columns and validation rules for each dataset.
- Keep exception records suitable for Excel/dashboard reporting.

## Testing Expectations

- Add or update tests for every meaningful implementation change.
- Prioritize tests for:
  - settlement-period mapping and coverage
  - daylight-saving edge cases
  - schema and data quality checks
  - synthetic data determinism
  - fleet requirement calculations
  - optimizer feasibility once implemented
  - settlement/P&L calculations once implemented
- Keep tests deterministic with fixed seeds and small fixtures.

## Reporting Expectations

- Excel reporting is a first-class deliverable in later phases.
- Planned workbook tabs:
  - Daily Summary
  - Market Prices
  - Fleet Requirements
  - Optimised Schedule
  - Dumb Charging Baseline
  - Forecast vs Actual
  - P&L / Settlement Exposure
  - Exceptions Log
  - Assumptions
- Dashboard views should be operational and decision-focused, not decorative.

## Product Language

Use language such as:

- EV flexibility trading operations
- daily trading support
- half-hourly settlement periods
- price-responsive charging
- operational constraints
- forecast-vs-actual reconciliation
- market participation metrics
- P&L-style reporting
- imbalance-style exposure
- exception management
- Excel/Python workflow automation

Avoid language such as:

- guaranteed trading profits
- production trading system
- live trading engine
- financial advice
- proprietary integration
- company endorsement

## Implementation Log

Update `docs/implementation_log.md` whenever meaningful work is completed. Include:

- date
- phase
- files changed
- main decisions
- tests run
- known limitations or next actions

## Git Hygiene

- Do not push to GitHub unless explicitly asked.
- Do not commit unless explicitly asked.
- Do not revert user changes unless explicitly asked.
- Keep generated sample files small and intentional.
- Do not commit bulky generated artifacts.
