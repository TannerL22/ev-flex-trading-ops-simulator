# Excel Report Guide

The Phase 6 workbook is generated at:

```text
data/outputs/ev_flex_daily_trading_report_sample.xlsx
```

It is a public demonstration workbook using synthetic/sample data. It is not a production trading, dispatch, or settlement system.

## Sheets

- `README`: workbook purpose, limitations, generated timestamp, and sheet descriptions.
- `Daily Summary`: headline KPIs for the base actuals scenario and comparison to high-deviation actuals.
- `Baseline vs Optimized`: dumb immediate-charge baseline versus site-cap optimized charging.
- `Scheduled vs Actual`: scheduled position compared with synthetic actual metered charging.
- `Settlement Exposure`: simplified settlement-style exposure, not official BSC settlement.
- `Market Metrics`: operational participation and deviation metrics.
- `Exceptions`: analyst-review queue with severity formatting.
- `Fleet Requirements`: synthetic fleet inputs and charging requirements.
- `Market Prices`: normalized synthetic/sample market prices.
- `Baseline Schedule`: immediate-charge vehicle schedule.
- `Optimized Schedule`: price-optimized vehicle schedule.
- `Actual Charging`: synthetic actual charging observations.
- `Assumptions`: model assumptions, units, and limitations.

## Interpretation

Use `Daily Summary` for the executive view, `Exceptions` for analyst review, and the data tabs for traceability. Cost outputs are P&L-style and settlement-style simulations only.
