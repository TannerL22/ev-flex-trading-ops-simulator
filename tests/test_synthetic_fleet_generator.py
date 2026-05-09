from __future__ import annotations

import pandas as pd

from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.fleet.synthetic_fleet_generator import generate_synthetic_fleet_schedule


def test_synthetic_fleet_generator_is_deterministic() -> None:
    first = generate_synthetic_fleet_schedule(
        service_date="2026-05-09",
        depot_id="DEPOT_A",
        n_vehicles=5,
        random_seed=123,
    )
    second = generate_synthetic_fleet_schedule(
        service_date="2026-05-09",
        depot_id="DEPOT_A",
        n_vehicles=5,
        random_seed=123,
    )

    pd.testing.assert_frame_equal(first, second)


def test_synthetic_fleet_generator_matches_required_columns() -> None:
    frame = generate_synthetic_fleet_schedule(service_date="2026-05-09", n_vehicles=3)

    assert set(
        [
            "service_date",
            "depot_id",
            "vehicle_id",
            "vehicle_type",
            "arrival_time",
            "departure_time",
            "battery_kwh",
            "start_soc_pct",
            "target_soc_pct",
            "max_charger_kw",
            "assigned_charger_id",
            "priority",
            "route_block",
        ]
    ).issubset(frame.columns)
    assert len(frame) == 3


def test_calculate_fleet_requirements_feasible_vehicle() -> None:
    frame = pd.DataFrame(
        [
            {
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
        ]
    )

    result = calculate_fleet_requirements(frame)

    assert result.loc[0, "required_kwh"] == 120
    assert result.loc[0, "available_charging_hours"] == 10
    assert result.loc[0, "feasibility_flag"] == "feasible"


def test_calculate_fleet_requirements_infeasible_vehicle() -> None:
    frame = pd.DataFrame(
        [
            {
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "vehicle_id": "EV-001",
                "vehicle_type": "single_deck_bus",
                "arrival_time": "2026-05-09T23:00:00+01:00",
                "departure_time": "2026-05-10T00:00:00+01:00",
                "battery_kwh": 400,
                "start_soc_pct": 10,
                "target_soc_pct": 90,
                "max_charger_kw": 50,
                "assigned_charger_id": "CHG-01",
                "priority": "high",
                "route_block": "RB-100",
            }
        ]
    )

    result = calculate_fleet_requirements(frame)

    assert result.loc[0, "required_kwh"] == 320
    assert result.loc[0, "feasibility_flag"] == "infeasible"


def test_calculate_fleet_requirements_zero_required_energy() -> None:
    frame = pd.DataFrame(
        [
            {
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "vehicle_id": "EV-001",
                "vehicle_type": "single_deck_bus",
                "arrival_time": "2026-05-09T20:00:00+01:00",
                "departure_time": "2026-05-10T06:00:00+01:00",
                "battery_kwh": 300,
                "start_soc_pct": 90,
                "target_soc_pct": 80,
                "max_charger_kw": 75,
                "assigned_charger_id": "CHG-01",
                "priority": "normal",
                "route_block": "RB-100",
            }
        ]
    )

    result = calculate_fleet_requirements(frame)

    assert result.loc[0, "required_kwh"] == 0
    assert result.loc[0, "feasibility_flag"] == "no_energy_required"
