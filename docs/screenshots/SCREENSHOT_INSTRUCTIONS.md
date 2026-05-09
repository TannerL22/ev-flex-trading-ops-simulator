# Screenshot Instructions

Automated screenshots are intentionally deferred to keep Phase 8 focused on repo polish and avoid adding browser automation complexity. Use these steps to capture consistent GitHub assets manually.

## Dashboard Screenshots

1. Run the dashboard:

   ```bash
   python scripts/run_full_demo_pipeline.py
   cd frontend
   npm install
   npm run dev
   ```

2. Open the local URL shown by Vite, usually `http://127.0.0.1:5173`.
3. Set browser zoom to 90% or 100%.
4. Use a desktop viewport around 1440 x 1000.
5. Use the left navigation and scenario selector to capture the polished React UI states.
6. Save screenshots to:

   ```text
   docs/screenshots/dashboard_overview.png
   docs/screenshots/baseline_vs_optimized.png
   docs/screenshots/scheduled_vs_actual.png
   docs/screenshots/settlement_exposure.png
   ```

Recommended captures:

- `dashboard_overview.png`: Overview page with `Base actuals`, KPI strip, hero chart, and disclaimer visible.
- `baseline_vs_optimized.png`: Baseline vs Optimized page with the site-cap optimized load profile.
- `scheduled_vs_actual.png`: Scheduled vs Actual page with `High deviation` selected.
- `settlement_exposure.png`: Settlement Exposure page with price lines and exposure bars.

## Excel Screenshots

Open:

```text
data/outputs/ev_flex_daily_trading_report_sample.xlsx
```

Capture:

- Daily Summary
- Baseline vs Optimized
- Scheduled vs Actual
- Exceptions

Before publishing screenshots, confirm no local absolute paths or private notes are visible.
