from __future__ import annotations

import pandas as pd

from ev_flex_trading.trading.position_builder import build_scheduled_position


def test_position_builder_aggregates_kwh_to_mwh() -> None:
    schedule = pd.DataFrame(
        [
            {
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "timestamp": "2026-05-09T00:00:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "charge_kwh": 50,
                "market": "synthetic_day_ahead",
                "source": "synthetic",
            },
            {
                "service_date": "2026-05-09",
                "depot_id": "DEPOT_A",
                "timestamp": "2026-05-09T00:00:00+01:00",
                "settlement_date": "2026-05-09",
                "settlement_period": 1,
                "charge_kwh": 25,
                "market": "synthetic_day_ahead",
                "source": "synthetic",
            },
        ]
    )

    position = build_scheduled_position(schedule, run_id="test")

    assert len(position) == 1
    assert position.loc[0, "scheduled_mwh"] == 0.075
    assert position.loc[0, "scheduled_kw"] == 150
    assert position.loc[0, "settlement_period"] == 1


def test_position_builder_empty_input() -> None:
    position = build_scheduled_position(pd.DataFrame(), run_id="test")

    assert position.empty
