from __future__ import annotations

import pandas as pd

from ev_flex_trading.trading.market_metrics import calculate_market_participation_metrics
from ev_flex_trading.trading.pnl_report import build_daily_pnl_style_summary


def test_daily_summary_realized_savings_and_delta() -> None:
    settlement = pd.DataFrame(
        [
            {
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "scheduled_mwh": 1.0,
                "actual_mwh": 1.1,
                "deviation_mwh": 0.1,
                "scheduled_cost_gbp": 50,
                "actual_energy_cost_gbp": 55,
                "imbalance_exposure_gbp": 5,
                "total_settlement_style_cost_gbp": 55,
            }
        ]
    )
    optimized_summary = pd.DataFrame(
        [
            {
                "vehicles_total": 2,
                "vehicle_readiness_pct": 100,
                "baseline_cost_gbp": 100,
                "optimized_cost_gbp": 50,
            }
        ]
    )
    reconciliation = pd.DataFrame(
        [
            {"reconciliation_status": "material_deviation"},
            {"reconciliation_status": "missing_actual"},
        ]
    )
    exceptions = pd.DataFrame([{"message": "x"}])

    summary = build_daily_pnl_style_summary(
        settlement,
        baseline_summary=optimized_summary,
        optimized_summary=optimized_summary,
        reconciliation=reconciliation,
        exceptions=exceptions,
        run_id="test",
        scenario="base",
    )

    assert summary.loc[0, "realized_savings_vs_baseline_gbp"] == 45
    assert summary.loc[0, "delta_vs_optimized_plan_gbp"] == 5
    assert summary.loc[0, "exception_count"] == 1


def test_market_metrics_counts_deviations_and_negative_prices() -> None:
    reconciliation = pd.DataFrame(
        [
            {
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "scheduled_mwh": 0.1,
                "actual_mwh": 0.12,
                "deviation_mwh": 0.02,
                "deviation_pct": 0.2,
                "scheduled_kw": 200,
                "actual_kw": 240,
                "reconciliation_status": "material_deviation",
            }
        ]
    )
    prices = pd.DataFrame(
        [{"settlement_date": "2026-05-09", "settlement_period": 1, "price_gbp_per_mwh": -5}]
    )

    metrics = calculate_market_participation_metrics(
        reconciliation,
        prices,
        run_id="test",
        scenario="base",
    )

    assert metrics.loc[0, "material_deviation_interval_count"] == 1
    assert metrics.loc[0, "intervals_with_negative_prices"] == 1
    assert metrics.loc[0, "intervals_with_positive_deviation"] == 1
