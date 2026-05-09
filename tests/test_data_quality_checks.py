from __future__ import annotations

import pandas as pd

from ev_flex_trading.ingestion.synthetic_market_generator import generate_synthetic_market_prices
from ev_flex_trading.validation.data_quality_checks import (
    check_fleet_schedule_quality,
    check_market_price_quality,
)


def _valid_fleet() -> pd.DataFrame:
    return pd.DataFrame(
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


def test_check_fleet_schedule_quality_returns_empty_for_valid_data() -> None:
    exceptions = check_fleet_schedule_quality(_valid_fleet(), run_id="test")

    assert exceptions.empty


def test_check_fleet_schedule_quality_detects_missing_columns() -> None:
    frame = _valid_fleet().drop(columns=["vehicle_id"])

    exceptions = check_fleet_schedule_quality(frame, run_id="test")

    assert not exceptions.empty
    assert "Missing required column: vehicle_id" in set(exceptions["message"])


def test_check_fleet_schedule_quality_detects_duplicates_and_soc_issue() -> None:
    frame = pd.concat([_valid_fleet(), _valid_fleet()], ignore_index=True)
    frame.loc[1, "target_soc_pct"] = 20

    exceptions = check_fleet_schedule_quality(frame, run_id="test")

    assert any(exceptions["message"].str.contains("Duplicate vehicle_id"))
    assert any(exceptions["message"].str.contains("target_soc_pct is below"))


def test_check_market_price_quality_detects_missing_and_duplicate_periods() -> None:
    frame = generate_synthetic_market_prices(
        service_date="2026-05-09",
        scenario="missing_intervals_for_validation_demo",
    )
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)

    exceptions = check_market_price_quality(frame, service_date="2026-05-09", run_id="test")

    assert any(exceptions["message"].str.contains("Missing half-hourly market interval"))
    assert any(exceptions["message"].str.contains("Duplicate settlement period"))
