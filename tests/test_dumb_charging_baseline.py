from __future__ import annotations

import pandas as pd

from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.optimisation.dumb_charging_baseline import (
    aggregate_depot_load,
    build_dumb_charging_baseline,
)


def _fleet_row(**overrides) -> dict[str, object]:  # noqa: ANN003
    row = {
        "service_date": "2026-05-09",
        "depot_id": "DEPOT_A",
        "vehicle_id": "EV-001",
        "vehicle_type": "single_deck_bus",
        "arrival_time": "2026-05-09T20:00:00+01:00",
        "departure_time": "2026-05-10T06:00:00+01:00",
        "battery_kwh": 300,
        "start_soc_pct": 40,
        "target_soc_pct": 80,
        "max_charger_kw": 75,
        "assigned_charger_id": "CHG-01",
        "priority": "normal",
        "route_block": "RB-100",
    }
    row.update(overrides)
    return row


def test_feasible_vehicle_charges_to_required_kwh() -> None:
    requirements = calculate_fleet_requirements(pd.DataFrame([_fleet_row()]))

    schedule, exceptions = build_dumb_charging_baseline(requirements, run_id="test")

    assert round(schedule["charge_kwh"].sum(), 6) == 120
    assert schedule.iloc[-1]["remaining_kwh_after_interval"] == 0
    assert exceptions.empty


def test_infeasible_vehicle_is_flagged() -> None:
    requirements = calculate_fleet_requirements(
        pd.DataFrame(
            [
                _fleet_row(
                    arrival_time="2026-05-09T23:00:00+01:00",
                    departure_time="2026-05-10T00:00:00+01:00",
                    battery_kwh=400,
                    start_soc_pct=10,
                    target_soc_pct=90,
                    max_charger_kw=50,
                )
            ]
        )
    )

    schedule, exceptions = build_dumb_charging_baseline(requirements, run_id="test")

    assert schedule["feasibility_flag"].eq("infeasible").all()
    assert any(exceptions["message"].str.contains("delivers less energy"))


def test_vehicle_stops_when_requirement_is_met() -> None:
    requirements = calculate_fleet_requirements(
        pd.DataFrame([_fleet_row(battery_kwh=100, start_soc_pct=50, target_soc_pct=60)])
    )

    schedule, _ = build_dumb_charging_baseline(requirements, run_id="test")

    assert len(schedule) == 1
    assert schedule.loc[0, "charge_kwh"] == 10
    assert schedule.loc[0, "charge_kw"] == 20


def test_zero_required_energy_handled_cleanly() -> None:
    requirements = calculate_fleet_requirements(
        pd.DataFrame([_fleet_row(start_soc_pct=85, target_soc_pct=80)])
    )

    schedule, exceptions = build_dumb_charging_baseline(requirements, run_id="test")

    assert len(schedule) == 1
    assert schedule.loc[0, "charge_kwh"] == 0
    assert schedule.loc[0, "feasibility_flag"] == "no_energy_required"
    assert exceptions.empty


def test_multiple_vehicles_aggregate_correctly() -> None:
    requirements = calculate_fleet_requirements(
        pd.DataFrame(
            [
                _fleet_row(vehicle_id="EV-001", assigned_charger_id="CHG-01"),
                _fleet_row(vehicle_id="EV-002", assigned_charger_id="CHG-02"),
            ]
        )
    )
    schedule, _ = build_dumb_charging_baseline(requirements, run_id="test")

    depot = aggregate_depot_load(schedule, run_id="test")

    assert depot.iloc[0]["total_charge_kwh"] == 75
    assert depot.iloc[0]["interval_kw"] == 150
    assert depot.iloc[0]["active_vehicle_count"] == 2
    assert depot.iloc[0]["charger_count_used"] == 2
