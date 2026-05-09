from __future__ import annotations

import pandas as pd

from ev_flex_trading.trading.settlement_simulator import simulate_settlement_style_exposure


def _reconciliation(deviation: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": "test",
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "timestamp": "2026-05-09T00:00:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "scheduled_mwh": 0.1,
                "actual_mwh": 0.1 + deviation,
                "deviation_mwh": deviation,
            }
        ]
    )


def _prices(price: float = 100) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "price_gbp_per_mwh": price,
            }
        ]
    )


def test_settlement_cost_calculation_for_positive_deviation() -> None:
    settlement, exceptions = simulate_settlement_style_exposure(
        _reconciliation(0.02),
        _prices(100),
        run_id="test",
    )

    assert settlement.loc[0, "scheduled_cost_gbp"] == 10
    assert settlement.loc[0, "imbalance_price_gbp_per_mwh"] == 125
    assert settlement.loc[0, "imbalance_exposure_gbp"] == 0.5
    assert exceptions.empty


def test_settlement_cost_calculation_for_negative_deviation() -> None:
    settlement, _ = simulate_settlement_style_exposure(
        _reconciliation(-0.02), _prices(100), run_id="test"
    )

    assert settlement.loc[0, "imbalance_price_gbp_per_mwh"] == 85
    assert settlement.loc[0, "imbalance_exposure_gbp"] == 0.3


def test_negative_market_price_handled() -> None:
    settlement, _ = simulate_settlement_style_exposure(
        _reconciliation(0.02), _prices(-10), run_id="test"
    )

    assert settlement.loc[0, "scheduled_cost_gbp"] == -1
    assert settlement.loc[0, "imbalance_price_gbp_per_mwh"] == 15


def test_missing_price_creates_exception() -> None:
    _, exceptions = simulate_settlement_style_exposure(
        _reconciliation(0.02),
        pd.DataFrame(columns=["settlement_date", "settlement_period", "price_gbp_per_mwh"]),
        run_id="test",
    )

    assert any(exceptions["message"].str.contains("Missing market price"))
