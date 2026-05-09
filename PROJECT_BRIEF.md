# Project Brief

## Overview

EV Flex Trading Ops Simulator is an independent public showcase of EV flexibility trading analytics. It demonstrates how a Python and Excel workflow can support daily analysis of EV fleet charging, market prices, forecast-vs-actual performance, and simplified settlement-style exposure.

The project is designed around a practical operational question:

> Given a fleet of EVs that must be charged by specific departure times, how should charging be scheduled against half-hourly market prices, and how should the resulting forecast, schedule, actual metered consumption, exceptions, and cost metrics be reported?

The project uses only public, synthetic, or sample data. It is not affiliated with any company, does not use proprietary systems or data, and is not a production trading or settlement platform.

## Why EV Charging Flexibility Matters

Depot-based EV fleets often have operational slack. Vehicles may arrive in the evening and depart the next morning, creating a charging window that can be optimized. The fleet still needs to meet readiness requirements, but the exact timing of charging can be flexible.

That flexibility creates an analytics problem:

- identify the energy each vehicle needs
- understand when each vehicle is available to charge
- normalize prices and operations to half-hourly settlement periods
- schedule charging within vehicle and charger constraints
- track actual metered charging versus the planned position
- surface exceptions that need analyst review
- explain daily cost and performance in a repeatable report

## Scope

The finished project should behave like a mini daily trading-support workflow, not just a chart of power prices.

Planned capabilities include:

- synthetic EV fleet schedule generation
- public/sample market price ingestion
- EPEX-style CSV loading for sample day-ahead or intraday prices
- optional ELEXON/BMRS and NESO public-data adapters
- GB half-hourly settlement-period normalization
- fleet charging requirement calculations
- immediate-charging baseline
- price-responsive charging optimization
- forecast-vs-actual reconciliation
- simplified imbalance-style exposure
- P&L-style reporting versus baseline
- structured exception management
- Excel daily report generation
- Streamlit operational dashboard

## Public Data Position

The project is intentionally reproducible and public-facing:

- EV fleet data is synthetic.
- Actual charging data is synthetic or sample data.
- Market data is public where available or represented by documented sample CSVs.
- No secrets, paid market feeds, employer data, or proprietary operational data are required.

## Analytical Outputs

The target outputs are designed for trading-support and commercial analytics review:

- total fleet energy requirement
- vehicle readiness and undercharge flags
- available charging windows
- site and charger utilization metrics
- market price curves by settlement period
- dumb versus smart charging cost comparison
- forecast-vs-actual charging error
- scheduled versus actual energy
- simplified imbalance-style exposure
- daily P&L-style cost versus baseline
- structured data quality and operational exceptions

## Current Phase

Phase 1 establishes the foundation:

- project packaging and configuration
- settlement-period utilities
- dataframe schemas
- synthetic EV fleet generation
- fleet requirement calculations
- basic data quality checks
- sample-data generation script
- tests for the foundation layer

Final polish, screenshots, and application-ready presentation materials are deferred to the final phase.

## Dumb Baseline vs Smart Optimization

The Phase 3 baseline represents a simple non-optimized operating approach: vehicles begin charging as soon as they are available and continue at their maximum available charger power until their required energy is delivered or the departure window closes.

This baseline is deliberately not price-responsive. Phase 4 adds smart charging optimization, where charging can be shifted across each vehicle's available plug-in window in response to prices while still respecting required energy, charger limits, and optional depot import capacity.

Baseline charging cost is calculated against normalized market prices, but it is not full trading P&L and does not include imbalance settlement, forecast-vs-actual reconciliation, or actual metered charging.

The optimized case is a simplified analytical model, not a production dispatch system. It demonstrates the commercial value of EV charging flexibility by comparing optimized charging cost, readiness, and peak import against the immediate-charge baseline.

## Trading-Support Reconciliation

Phase 5 turns the optimized site-cap schedule into a simplified scheduled position, then generates synthetic actual metered charging scenarios. The workflow reconciles scheduled energy versus actual charging by settlement period, flags material deviations and missing meter intervals, and calculates settlement-style exposure using a documented synthetic imbalance-price spread.

The output is a P&L-style daily summary for trading support. It reports scheduled MWh, actual MWh, deviations, expected savings versus baseline, realized savings after deviations, and exceptions requiring analyst review. This is not official settlement, real trading P&L, or trade execution.

## Excel Reporting Layer

Phase 6 packages the workflow into a professional Excel daily trading report. The workbook includes an executive daily summary, baseline-vs-optimized comparison, scheduled-vs-actual reconciliation, settlement-style exposure, market participation metrics, analyst-review exceptions, source data tabs, and assumptions.

The report is generated entirely from Python outputs and uses synthetic/sample data. It is designed to demonstrate Excel/Python workflow automation and stakeholder-ready trading-support reporting.

## Streamlit Dashboard Layer

Phase 7 adds a local Streamlit dashboard that reads the generated workflow outputs and presents the end-to-end daily process interactively. It shows fleet and market inputs, dumb baseline versus site-cap optimized charging, scheduled-vs-actual reconciliation, simplified settlement-style exposure, P&L-style daily summaries, market participation metrics, and analyst-review exceptions.

The dashboard is a public portfolio presentation layer. It does not execute trades, connect to live operational systems, or calculate official settlement.
