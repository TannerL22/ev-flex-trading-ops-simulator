# EV Flex Trading Ops Simulator

A Python, Excel, and React dashboard workflow for simulating EV fleet charging optimization, forecast-vs-actual reconciliation, and settlement-style trading support analytics.

## Overview

EV fleets create flexible electricity demand. Vehicles often return to depot hours before their next duty, so charging does not always need to happen immediately. If a vehicle must be ready by the morning, its charging can often be shifted across GB half-hourly settlement periods while still meeting operational readiness.

This project models that daily trading-support workflow. It compares a dumb immediate-charging baseline with a price-optimized smart charging schedule, then simulates actual metered deviations from the scheduled position.

The workflow estimates simplified settlement-style exposure, produces a P&L-style daily summary, and surfaces exceptions that an analyst would need to review. It generates both a professional Excel daily trading report and a polished local React dashboard. A Streamlit dashboard is retained as a lightweight fallback/data-review interface.

The project uses public, synthetic, and sample data only. It is independent, unaffiliated with any company, and is not a production trading, dispatch, or official settlement system.

The React dashboard is styled as a polished B2B analytics interface with a left navigation rail, top control bar, KPI strip, site-cap optimization hero chart, reconciliation views, exception review panel, and report downloads.

## Why It Matters

EV charging flexibility has direct commercial and operational relevance:

- reduce charging cost by shifting demand into cheaper periods
- manage depot peak import with a site capacity constraint
- preserve vehicle readiness by departure time
- reconcile scheduled charging against actual metered charging
- estimate settlement-style exposure from deviations
- create repeatable Python and Excel workflows for daily trading support
- surface data-quality and operational exceptions for analyst review

## Demo Outputs

Run the React dashboard:

```bash
python scripts/run_full_demo_pipeline.py
cd frontend
npm install
npm run dev
```

Generate the Excel report:

```bash
python scripts/generate_phase6_excel_report.py
```

Key outputs:

- Excel workbook: `data/outputs/ev_flex_daily_trading_report_sample.xlsx`
- React dashboard data: `frontend/public/data/dashboard.json`
- Dashboard guide: `docs/dashboard_guide.md`
- Excel report guide: `docs/excel_report_guide.md`
- Sample daily summaries: `data/outputs/phase5_daily_summary_base_sample.csv`
- Sample exceptions: `data/outputs/phase5_reconciliation_exceptions_sample.csv`
- Optimized schedule: `data/processed/optimized_vehicle_schedule_sample.csv`
- Reconciliation output: `data/processed/reconciliation_base_sample.csv`

## Key Sample Results

Base actuals scenario:

| Metric | Result |
| --- | ---: |
| Scheduled energy | 4.565 MWh |
| Actual energy | 4.557 MWh |
| Dumb baseline cost | £374.20 |
| Optimized expected cost | £237.09 |
| Settlement-style cost | £237.41 |
| Realized savings vs baseline | £136.78 / 36.6% |
| Vehicle readiness | 100% |
| Material deviation intervals | 0 |
| Missing meter intervals | 0 |

High-deviation scenario:

| Metric | Result |
| --- | ---: |
| Material deviation intervals | 6 |
| Missing meter intervals | 4 |
| Exceptions | 10 |

## Architecture

```text
Synthetic fleet + sample market data
        |
        v
Charging requirements and validation
        |
        +--> Dumb immediate-charge baseline
        |
        +--> Price-optimized smart charging
                    |
                    v
Scheduled position
        |
        v
Synthetic actual metered charging
        |
        v
Scheduled-vs-actual reconciliation
        |
        v
Settlement-style exposure + P&L-style summary
        |
        +--> Excel daily trading report
        |
        +--> React dashboard
```

## Tech Stack

- Python 3.11+
- pandas / numpy
- scipy.optimize.linprog
- pydantic
- xlsxwriter
- React / Vite / TypeScript
- Recharts
- Streamlit / Plotly fallback dashboard
- pytest
- ruff / black

## How To Run

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the package and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Regenerate the full demo pipeline:

```bash
python scripts/run_full_demo_pipeline.py
```

The GitHub repository includes an optional scheduled workflow that refreshes the synthetic/sample
demo outputs weekly and redeploys the Pages dashboard. It does not use live operational data or paid
market-data feeds.

Generate the Excel workbook:

```bash
python scripts/generate_phase6_excel_report.py
```

Run the dashboard:

```bash
cd frontend
npm install
npm run dev
```

Optional Streamlit fallback dashboard:

```bash
streamlit run app/streamlit_app.py
```

Run tests and quality checks:

```bash
python -m pytest
python -m ruff check .
python -m black --check .
```

## Repository Structure

```text
app/
  streamlit_app.py
frontend/
  src/
  public/data/dashboard.json
src/ev_flex_trading/
  actuals/
  dashboard/
  fleet/
  ingestion/
  optimisation/
  reporting/
  trading/
  utils/
  validation/
scripts/
  generate_phase*_*.py
  run_full_demo_pipeline.py
data/
  sample_inputs/
  processed/
  outputs/
docs/
  architecture.md
  dashboard_guide.md
  excel_report_guide.md
  runbook.md
tests/
```

## Methodology

The immediate-charging baseline charges each vehicle as soon as it is available, up to its charger limit, until the required energy is delivered or the charging window closes.

The smart charging optimizer uses a linear program to minimize energy cost across valid vehicle charging windows. The primary public-demo scenario includes a 750 kW site import cap, which makes the result more operationally realistic than an unconstrained cost-minimization case.

The actuals simulator creates synthetic metered charging scenarios. The reconciliation layer compares the scheduled position with actual metered charging by settlement period, classifies deviations, and produces structured exceptions.

Settlement-style exposure is calculated using a simplified imbalance-price spread. The P&L-style summary compares dumb baseline cost, optimized expected cost, and realized settlement-style cost after deviations.

## Limitations

- Uses synthetic/sample data only.
- Optimization model is simplified and intended for analytics demonstration.
- Settlement-style exposure is not official BSC settlement.
- P&L-style summary is illustrative and not real trading P&L.
- Scheduled position is a simplified proxy for traded energy.
- No live market or operational data is used.
- No trade execution, dispatch control, authentication, cloud deployment, or database backend.
- Local public demo only.

## License

MIT. See `LICENSE`.
