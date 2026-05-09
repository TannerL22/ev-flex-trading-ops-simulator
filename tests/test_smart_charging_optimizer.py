from __future__ import annotations

import pandas as pd

from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.optimisation.smart_charging_optimizer import optimize_smart_charging


def _fleet(**overrides) -> pd.DataFrame:  # noqa: ANN003
    row = {
        "service_date": "2026-05-09",
        "depot_id": "DEPOT_A",
        "vehicle_id": "EV-001",
        "vehicle_type": "bus",
        "arrival_time": "2026-05-09T00:00:00+01:00",
        "departure_time": "2026-05-09T01:00:00+01:00",
        "battery_kwh": 100,
        "start_soc_pct": 50,
        "target_soc_pct": 100,
        "max_charger_kw": 100,
        "assigned_charger_id": "CHG-01",
        "priority": "normal",
        "route_block": "RB-1",
    }
    row.update(overrides)
    return calculate_fleet_requirements(pd.DataFrame([row]))


def _prices(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": f"2026-05-09T00:{i * 30:02d}:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": i + 1,
                "price_gbp_per_mwh": value,
                "source": "synthetic",
                "market": "synthetic_day_ahead",
                "price_type": "synthetic",
                "data_quality_flag": "ok",
            }
            for i, value in enumerate(values)
        ]
    )


def test_one_vehicle_charges_in_cheaper_interval() -> None:
    schedule, _, _, exceptions = optimize_smart_charging(
        _fleet(target_soc_pct=75),
        _prices([100, 10]),
        run_id="test",
        market="synthetic_day_ahead",
    )

    assert schedule.iloc[0]["settlement_period"] == 2
    assert schedule["charge_kwh"].sum() == 25
    assert exceptions.empty


def test_respects_max_charger_power() -> None:
    schedule, _, _, _ = optimize_smart_charging(
        _fleet(target_soc_pct=100, max_charger_kw=50),
        _prices([10, 10]),
        run_id="test",
    )

    assert schedule["charge_kwh"].max() <= 25
    assert schedule["charge_kwh"].sum() == 50


def test_infeasible_vehicle_uses_unmet_slack_and_exception() -> None:
    schedule, _, _, exceptions = optimize_smart_charging(
        _fleet(target_soc_pct=100, max_charger_kw=20),
        _prices([10, 10]),
        run_id="test",
    )

    assert schedule["unmet_kwh"].max() == 30
    assert any(exceptions["message"].str.contains("unmet energy"))


def test_site_import_cap_is_respected() -> None:
    fleet = pd.concat(
        [
            _fleet(vehicle_id="EV-001", assigned_charger_id="CHG-01", target_soc_pct=75),
            _fleet(vehicle_id="EV-002", assigned_charger_id="CHG-02", target_soc_pct=75),
        ],
        ignore_index=True,
    )

    _, depot, _, _ = optimize_smart_charging(
        fleet,
        _prices([10, 10]),
        run_id="test",
        site_import_limit_kw=50,
    )

    assert depot["interval_kw"].max() <= 50 + 1e-6


def test_negative_price_interval_is_preferred() -> None:
    schedule, _, _, _ = optimize_smart_charging(
        _fleet(target_soc_pct=75),
        _prices([50, -20]),
        run_id="test",
    )

    assert schedule.iloc[0]["settlement_period"] == 2


def test_optimizer_handles_overnight_windows() -> None:
    fleet = _fleet(
        arrival_time="2026-05-09T23:30:00+01:00",
        departure_time="2026-05-10T00:30:00+01:00",
        target_soc_pct=75,
    )
    prices = pd.DataFrame(
        [
            {
                "timestamp": "2026-05-09T23:30:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 48,
                "price_gbp_per_mwh": 80,
                "source": "synthetic",
                "market": "synthetic_day_ahead",
                "price_type": "synthetic",
                "data_quality_flag": "ok",
            },
            {
                "timestamp": "2026-05-10T00:00:00+01:00",
                "settlement_date": "2026-05-10",
                "settlement_period": 1,
                "price_gbp_per_mwh": 20,
                "source": "synthetic",
                "market": "synthetic_day_ahead",
                "price_type": "synthetic",
                "data_quality_flag": "ok",
            },
        ]
    )

    schedule, _, _, _ = optimize_smart_charging(fleet, prices, run_id="test")

    assert schedule.iloc[0]["settlement_date"] == "2026-05-10"


def test_missing_price_interval_creates_exception() -> None:
    schedule, _, _, exceptions = optimize_smart_charging(
        _fleet(target_soc_pct=100),
        _prices([10]),
        run_id="test",
    )

    assert any(exceptions["message"].str.contains("Missing market price"))
    assert schedule["unmet_kwh"].max() == 0


def test_solver_output_has_no_material_negative_charge() -> None:
    schedule, _, _, _ = optimize_smart_charging(
        _fleet(target_soc_pct=100),
        _prices([10, 11]),
        run_id="test",
    )

    assert (schedule["charge_kwh"] >= -1e-6).all()
