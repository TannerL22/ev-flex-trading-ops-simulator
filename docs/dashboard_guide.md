# Dashboard Guide

The React dashboard is the primary local presentation layer for the EV Flex Trading Ops Simulator. It reads a static JSON payload exported from generated Phase 1-6 outputs and presents the daily workflow as an operational review pack.

The UI is designed to feel like a premium B2B analytics dashboard: left navigation, top controls, KPI cards, chart-first panels, visible exceptions, and public-safe limitations.

Generate the dashboard data from the project root:

```bash
python scripts/run_full_demo_pipeline.py
```

Run the React app:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://127.0.0.1:5173`.

The Streamlit dashboard remains available as a fallback/data-review interface:

```bash
streamlit run app/streamlit_app.py
```

## Recommended Demo Flow

1. Start on **Overview**. The KPI strip should make the run understandable in under a minute: scheduled MWh, actual MWh, settlement-style cost, baseline cost, optimized expected cost, realized savings, readiness, and material exceptions.
2. Use the hero **Baseline vs Optimized Charging Load** panel to explain immediate charging versus site-cap optimized charging.
3. Use **Scheduled vs Actual Charging** to show close base-case tracking, then switch the scenario selector to `High deviation`.
4. Use **Settlement Exposure** to explain simplified deviation pricing. Use careful wording: this is not official settlement.
5. Use **Exceptions** to show the analyst review queue and suggested actions.
6. Open **Data Tables / Downloads** to reference the generated Excel report.

## Screenshot Checklist

Create `docs/screenshots/` when screenshots are ready and capture:

- Overview with base actuals selected.
- Baseline vs Optimized load profile.
- Scheduled vs Actual with high-deviation selected.
- Exceptions table filtered to high or medium severity.
- Excel workbook Daily Summary sheet.

## Limitations

- The dashboard uses synthetic/sample data.
- Settlement-style exposure is simplified and not official BSC settlement.
- P&L-style summary is illustrative and not real trading P&L.
- The scheduled position is a simplified proxy for traded energy.
- There is no live operational data, real trade execution, user authentication, cloud deployment, or database backend.
- The React app is a local static presentation layer. It does not execute analytics in the browser.
- Streamlit remains available as a fallback, but the React dashboard is the preferred public demo.
