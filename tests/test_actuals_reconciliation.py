from __future__ import annotations

import pandas as pd

from ev_flex_trading.actuals.actuals_reconciliation import reconcile_scheduled_vs_actual


def _position() -> pd.DataFrame:
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
                "scheduled_kw": 200,
                "market": "synthetic",
                "source": "synthetic",
                "position_type": "optimized",
                "notes": "",
            }
        ]
    )


def _actual(kwh: float | None, quality: str = "ok") -> pd.DataFrame:
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
                "scheduled_charge_kwh": 100,
                "actual_charge_kwh": kwh,
                "actual_charge_kw": None if kwh is None else kwh / 0.5,
                "meter_quality_flag": quality,
                "actuals_scenario": "test",
                "disruption_type": "none",
                "notes": "",
            }
        ]
    )


def test_exact_match_produces_matched_status() -> None:
    reconciliation, exceptions = reconcile_scheduled_vs_actual(
        _position(), _actual(100), run_id="test"
    )

    assert reconciliation.loc[0, "reconciliation_status"] == "matched"
    assert exceptions.empty


def test_small_deviation_produces_minor_status() -> None:
    reconciliation, _ = reconcile_scheduled_vs_actual(_position(), _actual(103), run_id="test")

    assert reconciliation.loc[0, "reconciliation_status"] == "minor_deviation"


def test_large_deviation_produces_material_status() -> None:
    reconciliation, exceptions = reconcile_scheduled_vs_actual(
        _position(), _actual(50), run_id="test"
    )

    assert reconciliation.loc[0, "reconciliation_status"] == "material_deviation"
    assert not exceptions.empty


def test_missing_actual_produces_missing_status() -> None:
    reconciliation, exceptions = reconcile_scheduled_vs_actual(
        _position(),
        _actual(None, quality="missing"),
        run_id="test",
    )

    assert reconciliation.loc[0, "reconciliation_status"] == "missing_actual"
    assert any(exceptions["message"].str.contains("missing_actual"))


def test_duplicate_actuals_are_flagged() -> None:
    actuals = pd.concat([_actual(50), _actual(50)], ignore_index=True)

    _, exceptions = reconcile_scheduled_vs_actual(_position(), actuals, run_id="test")

    assert any(exceptions["message"].str.contains("Duplicate actual meter interval"))
