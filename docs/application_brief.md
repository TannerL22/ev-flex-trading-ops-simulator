# EV Flex Trading Ops Simulator

**One-sentence summary:** A public Python, Excel, and React dashboard project that simulates EV fleet charging optimisation, scheduled-vs-actual reconciliation, settlement-style exposure, and daily trading-support reporting using synthetic/sample data.

## Problem

EV fleets create flexible electricity demand. Vehicles often need to be charged by fixed departure times, but the charging itself can be shifted across half-hourly periods. That flexibility can reduce energy cost, manage depot peak import, preserve operational readiness, and create a repeatable daily workflow for trading-support analytics.

## What The Project Does

The project models a simplified daily EV flexibility workflow:

```text
Fleet requirements
  -> half-hourly market prices
  -> immediate-charging baseline
  -> price-optimised charging schedule
  -> scheduled position
  -> synthetic actual metered charging
  -> scheduled-vs-actual reconciliation
  -> settlement-style / P&L-style reporting
  -> exception review queue
```

The primary demo scenario uses a site import cap so the optimised schedule remains commercially realistic rather than simply pushing all charging into the cheapest intervals.

## Tools Used

- Python for workflow automation and analytics
- pandas and numpy for data processing
- scipy linear programming for smart charging optimisation
- pydantic and structured checks for validation
- xlsxwriter for the Excel daily trading report
- React, Vite, and Recharts for the public dashboard
- pytest, ruff, black, and GitHub Actions for quality checks and repeatable deployment

## Role-Relevant Capabilities Demonstrated

- **Data processing:** normalises fleet, market-price, charging, reconciliation, and exception data into reusable schemas.
- **Python automation:** runs the end-to-end daily workflow from generated inputs to dashboard/Excel outputs.
- **Excel tooling:** creates a professional daily trading report with KPIs, schedules, exposure, metrics, assumptions, and exceptions.
- **Trading support:** compares immediate charging with price-responsive charging under operational constraints.
- **Forecast-vs-actual:** reconciles scheduled energy against synthetic metered actuals by settlement period.
- **Settlement-style reporting:** estimates simplified deviation exposure and P&L-style daily cost impacts without claiming official settlement.

## Public Data Disclaimer

This is an independent public portfolio project using synthetic/sample data. It is not affiliated with any company, does not use proprietary operational data, does not execute trades, and is not a production trading, dispatch, or official settlement system.
