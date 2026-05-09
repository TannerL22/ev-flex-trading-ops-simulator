from __future__ import annotations

import pandas as pd

from ev_flex_trading.trading.optimization_comparison import (
    build_optimization_summary,
    count_materially_shifted_intervals,
)


def _vehicle_schedule(unmet: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "vehicle_id": "EV-001",
                "timestamp": "2026-05-09T00:00:00+01:00",
                "required_kwh": 100,
                "unmet_kwh": unmet,
            }
        ]
    )


def _load(total_mwh: float, interval_kw: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "total_charge_kwh": total_mwh * 1000,
                "total_charge_mwh": total_mwh,
                "interval_kw": interval_kw,
            }
        ]
    )


def _cost(total_mwh: float, cost: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "total_charge_mwh": total_mwh,
                "interval_cost_gbp": cost,
            }
        ]
    )


def test_optimization_summary_calculates_savings_and_peak_reduction() -> None:
    summary = build_optimization_summary(
        optimized_vehicle_schedule=_vehicle_schedule(),
        optimized_depot_load=_load(1.0, 100),
        optimized_cost_by_interval=_cost(1.0, 50),
        baseline_vehicle_schedule=pd.DataFrame(),
        baseline_depot_load=_load(1.0, 200),
        baseline_cost_by_interval=_cost(1.0, 80),
        run_id="test",
        service_date="2026-05-09",
        depot_id="DEPOT_A",
        site_import_limit_kw=None,
        exception_count=0,
    )

    assert summary.loc[0, "savings_gbp"] == 30
    assert summary.loc[0, "savings_pct"] == 37.5
    assert summary.loc[0, "peak_reduction_kw"] == 100
    assert summary.loc[0, "vehicle_readiness_pct"] == 100


def test_optimization_summary_handles_undercharged_case() -> None:
    summary = build_optimization_summary(
        optimized_vehicle_schedule=_vehicle_schedule(unmet=25),
        optimized_depot_load=_load(0.075, 75),
        optimized_cost_by_interval=_cost(0.075, 5),
        baseline_vehicle_schedule=pd.DataFrame(),
        baseline_depot_load=_load(0.1, 100),
        baseline_cost_by_interval=_cost(0.1, 10),
        run_id="test",
        service_date="2026-05-09",
        depot_id="DEPOT_A",
        site_import_limit_kw=75,
        exception_count=1,
    )

    assert summary.loc[0, "vehicles_undercharged"] == 1
    assert summary.loc[0, "total_unmet_mwh"] == 0.025


def test_materially_shifted_interval_count() -> None:
    baseline = pd.DataFrame(
        [
            {"settlement_date": "2026-05-09", "settlement_period": 1, "total_charge_kwh": 50},
            {"settlement_date": "2026-05-09", "settlement_period": 2, "total_charge_kwh": 0},
        ]
    )
    optimized = pd.DataFrame(
        [
            {"settlement_date": "2026-05-09", "settlement_period": 1, "total_charge_kwh": 0},
            {"settlement_date": "2026-05-09", "settlement_period": 2, "total_charge_kwh": 50},
        ]
    )

    assert count_materially_shifted_intervals(baseline, optimized) == 2
