"""Build scheduled energy positions from optimized schedules."""

from __future__ import annotations

import pandas as pd


def build_scheduled_position(
    optimized_vehicle_schedule: pd.DataFrame,
    *,
    run_id: str = "phase5_position",
    position_type: str = "site_cap_optimized_schedule",
) -> pd.DataFrame:
    """Aggregate an optimized vehicle schedule into a half-hourly scheduled position."""

    columns = [
        "run_id",
        "service_date",
        "depot_id",
        "timestamp",
        "settlement_date",
        "settlement_period",
        "scheduled_mwh",
        "scheduled_kw",
        "market",
        "source",
        "position_type",
        "notes",
    ]
    if optimized_vehicle_schedule.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        optimized_vehicle_schedule.groupby(
            ["service_date", "depot_id", "timestamp", "settlement_date", "settlement_period"],
            dropna=False,
        )
        .agg(
            scheduled_kwh=("charge_kwh", "sum"),
            market=("market", "first"),
            source=("source", "first"),
        )
        .reset_index()
    )
    grouped["run_id"] = run_id
    grouped["scheduled_mwh"] = grouped["scheduled_kwh"] / 1000.0
    grouped["scheduled_kw"] = grouped["scheduled_kwh"] / 0.5
    grouped["position_type"] = position_type
    grouped["notes"] = "Simplified scheduled energy position from optimized charging schedule."
    return grouped[columns]
