# Demo Script

## Two-Minute Walkthrough

**Opening**

This project simulates a daily trading-support workflow for an EV fleet. The core question is: given vehicles that need to be charged by departure, market prices by half-hourly settlement period, and operational constraints, how should charging be scheduled and reconciled after actual metered data arrives?

**Fleet and Market Inputs**

The workflow starts with synthetic EV fleet requirements: arrival and departure windows, battery sizes, start and target state of charge, charger limits, and route priorities. Market prices are synthetic/sample data normalized to GB half-hourly settlement periods.

**Baseline vs Optimized**

The dumb baseline charges vehicles immediately when they arrive. The smart schedule uses linear optimization to shift charging into cheaper periods while respecting vehicle windows, charger limits, and a 750 kW site import cap. In the base sample, this reduces cost from about £374 to about £237 while keeping 100% vehicle readiness.

**Scheduled vs Actual**

The optimized schedule becomes the scheduled position. The actuals simulator then creates metered charging scenarios. In the base case, actual charging closely follows the schedule. In the high-deviation case, missing meter intervals and material deviations are flagged for analyst review.

**Settlement-Style Exposure and Exceptions**

The reconciliation feeds a simplified settlement-style exposure calculation. This is not official settlement; it is an analytical estimate of how deviations affect daily cost. Exceptions are structured by severity, category, entity, message, and suggested action.

**Excel Report**

The Python workflow generates a professional Excel report with daily summary, baseline-vs-optimized comparison, scheduled-vs-actual reconciliation, settlement-style exposure, market metrics, exceptions, data tabs, and assumptions.

**Close**

The project demonstrates EV flexibility analytics, Python automation, optimization, Excel reporting, Streamlit dashboarding, and the discipline needed for daily trading-support workflows.

## 30-Second Version

This is a public EV flexibility trading analytics simulator. It generates synthetic fleet and market data, compares immediate charging against price-optimized charging, simulates actual metered deviations, reconciles scheduled versus actual energy, estimates settlement-style exposure, and produces both an Excel daily report and Streamlit dashboard. It uses synthetic/sample data only and is not a production trading or settlement system.

## Five-Minute Expanded Version

1. Start on the Streamlit Overview tab and explain the headline KPIs.
2. Open Fleet & Market Inputs to show vehicle requirements and half-hourly prices.
3. Open Baseline vs Optimized to explain immediate charging versus linear optimization with a site import cap.
4. Switch between `base_actuals` and `high_deviation` to show why reconciliation and exceptions matter.
5. Open Settlement Exposure to explain deviation pricing and the P&L-style summary.
6. Open Exceptions to show analyst-review workflow.
7. Open the Excel workbook and show Daily Summary, Baseline vs Optimized, Scheduled vs Actual, Exceptions, and Assumptions.
8. Close by explaining how the code is modular, tested, and reproducible.

## Likely Interview Questions

**Why use synthetic data?**

The project is intended to be public and reproducible. Synthetic/sample data avoids confidentiality issues while still demonstrating the workflow, data model, and analytics logic.

**Why use a site import cap?**

Without a depot cap, the optimizer can create unrealistic peak charging. The 750 kW cap makes the demo more operationally credible by showing cost optimization under a practical network or site constraint.

**Is this real settlement?**

No. It is a simplified settlement-style exposure model for analytics demonstration. Official settlement would require full market rules, validated metering, contractual context, and official data sources.

**How does the optimizer work?**

It uses a linear program where decision variables represent vehicle charging energy by half-hour interval. The objective minimizes energy cost while respecting plug-in windows, charger limits, required energy, and optional site import capacity.

**What would you improve next?**

I would add richer charger conflict resolution, live public data adapters, a database-backed run history, more robust scenario configuration, and deployment packaging.

**How would this connect to live ELEXON/EPEX/NESO data?**

The project already separates ingestion adapters from normalization. Live integrations would be added behind those adapters with explicit validation, retry handling, source metadata, and offline fallbacks.

**How would this scale in production?**

I would separate orchestration, storage, validation, optimization, reporting, and monitoring. A production version would use managed data storage, scheduled jobs, observability, access control, and formal data contracts.

**What are the limitations?**

It uses synthetic/sample data, simplified charger/site constraints, simplified settlement-style exposure, and no live trading or operational integrations. It is a portfolio analytics demo, not a production system.
