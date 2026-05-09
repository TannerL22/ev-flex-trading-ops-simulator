# GitHub Presentation Checklist

## Final Pre-Push Checklist

- Run `python scripts/run_full_demo_pipeline.py`.
- Run `python scripts/generate_phase6_excel_report.py`.
- Run `python scripts/public_safety_scan.py`.
- Run `python -m pytest`.
- Run `python -m ruff check .`.
- Run `python -m black --check .`.
- Run `cd frontend && npm install && npm run build`.
- Run `cd frontend && npm run dev` and confirm the React dashboard opens locally.
- Optionally run `streamlit run app/streamlit_app.py` to confirm the fallback dashboard opens locally.
- Confirm `.github/workflows/refresh-demo-data.yml` is enabled if you want weekly synthetic/sample
  demo-data refreshes and Pages redeployment.
- Confirm the polished React dashboard UI shows the navy sidebar, top controls, KPI strip, baseline-vs-optimized hero chart, exceptions panel, outputs/downloads card, and visible public-demo disclaimer.
- Confirm `LICENSE` is present and says MIT.
- Confirm README is final and public-facing.
- Confirm `docs/application_project_brief.md`, `docs/demo_script.md`, and `docs/runbook.md` are present.
- Confirm screenshots are added or `docs/screenshots/SCREENSHOT_INSTRUCTIONS.md` is present.
- Confirm the Excel workbook is generated at `data/outputs/ev_flex_daily_trading_report_sample.xlsx`.
- Confirm sample outputs are small and synthetic/sample-only.
- Confirm no `.env`, private notes, caches, virtual environments, build artifacts, or local IDE folders are included.
- Confirm no local absolute paths are present in public docs or generated manifests.

## Public-Safety Wording

Use:

- independent public showcase project
- synthetic/sample data
- EV flexibility trading analytics
- daily trading-support workflow simulation
- settlement-style exposure
- P&L-style summary
- scheduled position
- not production trading, dispatch, or official settlement
- no live operational data
- no real trade execution

Avoid:

- affiliation claims
- proprietary data claims
- official settlement claims
- real trading P&L claims
- production trading system claims
- private application strategy
- employer-private details
- colleague, lender, transaction, or internal project references

## Generated Output Policy

Commit small public sample inputs and small processed demo outputs when they help reviewers run or understand the project.

Current intended public demo outputs include:

- synthetic fleet schedule
- synthetic/sample market prices
- baseline and optimized charging schedules
- actual charging and reconciliation samples
- settlement-style exposure samples
- daily summary and exception samples
- sample Excel workbook
- report manifest with repo-relative paths

Do not commit:

- bulky raw downloads
- paid/proprietary data
- credentials
- local caches
- one-off debug outputs
- private notes

## Screenshot Checklist

- Dashboard Overview with base actuals.
- Baseline vs Optimized load profile.
- Scheduled vs Actual with high-deviation selected.
- Settlement Exposure or Exceptions tab.
- Excel Daily Summary sheet.
- Excel Exceptions or Assumptions sheet.

Suggested README screenshot placement:

- Add one dashboard overview image near the top after the overview section.
- Add one Excel report image near the Demo Outputs section.
- Keep images under `docs/screenshots/`.

## Suggested Repository Description

`EV flexibility trading analytics simulator with Python optimization, Excel reporting, and React dashboard.`

## Suggested GitHub Topics

- `energy-trading`
- `ev-flexibility`
- `battery-storage`
- `optimization`
- `streamlit`
- `react`
- `vite`
- `electricity-markets`
- `python`
- `excel-reporting`

## Suggested First Commit Message

`Initial public EV flexibility trading analytics simulator`
