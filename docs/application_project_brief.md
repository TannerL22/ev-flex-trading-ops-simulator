# EV Flex Trading Ops Simulator

## One-Sentence Summary

I built a Python, Excel, and React dashboard project that simulates EV fleet charging optimization, scheduled-vs-actual reconciliation, and settlement-style trading support analytics using synthetic/sample data.

## Problem Statement

Depot-based EV fleets often have flexible charging demand. Vehicles need to be ready by departure, but charging can often be shifted across half-hourly periods to reduce cost, manage peak import, and support market-facing operational decisions.

## What I Built

The project creates a reproducible daily workflow:

- generate synthetic EV fleet requirements
- normalize market prices to GB half-hourly settlement periods
- calculate required vehicle energy and feasibility
- compare immediate charging with price-optimized smart charging
- simulate actual metered charging deviations
- reconcile scheduled versus actual energy
- estimate simplified settlement-style exposure
- generate an Excel daily trading report
- present the workflow in a public React dashboard

## Key Capabilities

- EV fleet charging requirement analysis
- Linear optimization using `scipy.optimize.linprog`
- Site import cap scenario for operational realism
- Scheduled-vs-actual reconciliation
- Structured exception management
- P&L-style daily summary
- Excel reporting automation with `xlsxwriter`
- React dashboard with scenario selection
- Automated tests and reproducible sample outputs

## Sample Results

Base actuals scenario:

- Scheduled energy: 4.565 MWh
- Actual energy: 4.557 MWh
- Dumb baseline cost: £374.20
- Optimized expected cost: £237.09
- Settlement-style cost: £236.98
- Realized savings vs baseline: £137.22 / 36.7%
- Vehicle readiness: 100%

High-deviation scenario:

- 6 material deviation intervals
- 4 missing meter intervals
- 10 exceptions for analyst review

## Technical Stack

Python, pandas, numpy, scipy, pydantic, xlsxwriter, React, Vite, Recharts, Streamlit fallback, pytest, ruff, and black.

## Relevance to Energy Trading and Commercial Analytics

The project demonstrates how market data, operational fleet constraints, optimization, exception management, and stakeholder reporting can be combined into a repeatable daily trading-support workflow. It is designed to show the analytical layer that helps transform messy operational and market inputs into decision-useful reporting.

## Public Demo Status and Limitations

This is an independent public showcase project using synthetic/sample data. It is not a production trading, dispatch, or official settlement system. It does not use live operational data, execute trades, or calculate official BSC settlement.

## References

- GitHub repository: `https://github.com/TannerL22/ev-flex-trading-ops-simulator`
- Live dashboard: `https://tannerl22.github.io/ev-flex-trading-ops-simulator/`
- Local React dashboard command: `cd frontend && npm run dev`
- Excel report: `data/outputs/ev_flex_daily_trading_report_sample.xlsx`
