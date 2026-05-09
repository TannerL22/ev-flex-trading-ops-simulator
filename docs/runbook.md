# Runbook

This runbook explains how to reproduce the local EV Flex Trading Ops Simulator demo from a clean checkout.

## Clean Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the project:

```bash
python -m pip install -e ".[dev]"
```

## Regenerate All Sample Outputs

Run the full demo pipeline:

```bash
python scripts/run_full_demo_pipeline.py
```

This runs:

1. `scripts/generate_phase1_sample_data.py`
2. `scripts/generate_phase2_market_data.py`
3. `scripts/generate_phase3_baseline.py`
4. `scripts/generate_phase4_optimized_schedule.py`
5. `scripts/generate_phase5_trading_reconciliation.py`
6. `scripts/generate_phase6_excel_report.py`
7. `scripts/export_dashboard_json.py`

The GitHub repository also includes a scheduled workflow,
`.github/workflows/refresh-demo-data.yml`, which regenerates the synthetic/sample demo outputs
weekly and can be run manually from the Actions tab. It does not call live or paid market APIs.

## Generate Excel Workbook

```bash
python scripts/generate_phase6_excel_report.py
```

Output:

```text
data/outputs/ev_flex_daily_trading_report_sample.xlsx
```

## Run React Dashboard

The React dashboard is the preferred public demo interface.

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://127.0.0.1:5173`.

If dashboard inputs are missing, return to the project root and rerun:

```bash
python scripts/run_full_demo_pipeline.py
```

## Run Streamlit Fallback Dashboard

```bash
streamlit run app/streamlit_app.py
```

If the dashboard warns about missing files, rerun the full demo pipeline or the Phase 6 report script.

## Run Tests and Quality Checks

```bash
python -m pytest
python -m ruff check .
python -m black --check .
python scripts/public_safety_scan.py
cd frontend
npm run build
```

## Troubleshooting

If React dependencies are missing, install them from `frontend/`:

```bash
npm install
```

If `streamlit` or `plotly` is missing, reinstall the Python project:

```bash
python -m pip install -e ".[dev]"
```

If generated CSVs are stale or missing, rerun:

```bash
python scripts/run_full_demo_pipeline.py
```

If Excel tests fail because `openpyxl` is missing, reinstall development dependencies with `python -m pip install -e ".[dev]"`.

The workflow does not require internet access and does not call live APIs during tests.
