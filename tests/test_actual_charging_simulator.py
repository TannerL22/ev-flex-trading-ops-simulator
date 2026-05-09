from __future__ import annotations

import pandas as pd

from ev_flex_trading.actuals.actual_charging_simulator import simulate_actual_charging


def _schedule() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": "test",
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "vehicle_id": "EV-001",
                "assigned_charger_id": "CHG-01",
                "timestamp": "2026-05-09T00:00:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "interval_hours": 0.5,
                "charge_kw": 100,
                "charge_kwh": 50,
            },
            {
                "run_id": "test",
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "vehicle_id": "EV-001",
                "assigned_charger_id": "CHG-01",
                "timestamp": "2026-05-09T00:30:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 2,
                "interval_hours": 0.5,
                "charge_kw": 100,
                "charge_kwh": 50,
            },
        ]
    )


def test_base_actuals_roughly_follow_schedule_and_are_reproducible() -> None:
    first = simulate_actual_charging(_schedule(), random_seed=1, scenario="base_actuals")
    second = simulate_actual_charging(_schedule(), random_seed=1, scenario="base_actuals")

    assert first["actual_charge_kwh"].sum() > 95
    assert first["actual_charge_kwh"].sum() < 105
    pd.testing.assert_frame_equal(first, second)


def test_actuals_are_not_negative() -> None:
    actuals = simulate_actual_charging(_schedule(), random_seed=2, scenario="high_deviation")

    assert (actuals["actual_charge_kwh"].dropna() >= 0).all()


def test_missing_meter_scenario_marks_missing_intervals() -> None:
    actuals = simulate_actual_charging(_schedule(), random_seed=3, scenario="missing_meter_data")

    assert actuals["meter_quality_flag"].eq("missing").any()


def test_derating_reduces_actual_charging() -> None:
    base = simulate_actual_charging(_schedule(), random_seed=4, scenario="base_actuals")
    derated = simulate_actual_charging(_schedule(), random_seed=4, scenario="charger_derating")

    assert derated["actual_charge_kwh"].sum(skipna=True) < base["actual_charge_kwh"].sum(
        skipna=True
    )
