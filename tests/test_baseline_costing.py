from __future__ import annotations

import pandas as pd

from ev_flex_trading.trading.baseline_costing import calculate_baseline_charging_cost


def _depot_load() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": "test",
                "timestamp": "2026-05-09T00:00:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "depot_id": "DEPOT_A",
                "total_charge_kwh": 100,
                "total_charge_mwh": 0.1,
                "average_charge_kw": 200,
                "interval_kw": 200,
                "active_vehicle_count": 2,
                "charger_count_used": 2,
            },
            {
                "run_id": "test",
                "timestamp": "2026-05-09T00:30:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 2,
                "depot_id": "DEPOT_A",
                "total_charge_kwh": 50,
                "total_charge_mwh": 0.05,
                "average_charge_kw": 100,
                "interval_kw": 100,
                "active_vehicle_count": 1,
                "charger_count_used": 1,
            },
        ]
    )


def _market_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "price_gbp_per_mwh": 100,
                "market": "synthetic_day_ahead",
                "source": "synthetic",
                "price_type": "synthetic",
                "data_quality_flag": "ok",
            },
            {
                "settlement_date": "2026-05-09",
                "settlement_period": 2,
                "price_gbp_per_mwh": 50,
                "market": "synthetic_day_ahead",
                "source": "synthetic",
                "price_type": "synthetic",
                "data_quality_flag": "ok",
            },
        ]
    )


def test_baseline_costing_calculates_interval_and_weighted_cost() -> None:
    cost, summary, exceptions = calculate_baseline_charging_cost(
        _depot_load(),
        _market_prices(),
        run_id="test",
    )

    assert cost["interval_cost_gbp"].sum() == 12.5
    assert summary.loc[0, "total_baseline_cost_gbp"] == 12.5
    assert round(summary.loc[0, "weighted_avg_price_gbp_per_mwh"], 6) == round(12.5 / 0.15, 6)
    assert exceptions.empty


def test_missing_price_interval_creates_exception() -> None:
    prices = _market_prices().iloc[[0]]

    cost, summary, exceptions = calculate_baseline_charging_cost(
        _depot_load(),
        prices,
        run_id="test",
    )

    assert cost["price_gbp_per_mwh"].isna().sum() == 1
    assert summary.loc[0, "missing_price_intervals"] == 1
    assert any(exceptions["message"].str.contains("Missing market price"))


def test_negative_price_reduces_baseline_cost() -> None:
    prices = _market_prices()
    prices.loc[1, "price_gbp_per_mwh"] = -20

    cost, summary, exceptions = calculate_baseline_charging_cost(
        _depot_load(),
        prices,
        run_id="test",
    )

    assert cost["interval_cost_gbp"].sum() == 9.0
    assert summary.loc[0, "total_baseline_cost_gbp"] == 9.0
    assert exceptions.empty
