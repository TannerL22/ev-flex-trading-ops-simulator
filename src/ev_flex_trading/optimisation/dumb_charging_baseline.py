"""Immediate-charge baseline scheduler."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ev_flex_trading.fleet.charging_windows import build_charging_window_intervals
from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception

BASELINE_STRATEGY = "immediate_charge"


def build_dumb_charging_baseline(
    fleet_requirements: pd.DataFrame,
    *,
    efficiency: float = 1.0,
    run_id: str = "phase3_baseline",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a vehicle-level immediate-charge baseline schedule."""

    if efficiency <= 0 or efficiency > 1:
        raise ValueError("efficiency must be > 0 and <= 1")

    requirements = (
        fleet_requirements.copy()
        if "required_kwh" in fleet_requirements.columns
        else calculate_fleet_requirements(fleet_requirements)
    )
    records = []
    exception_records = []
    now = datetime.now(timezone.utc)

    for row in requirements.itertuples(index=False):
        vehicle_id = row.vehicle_id
        required_kwh = float(row.required_kwh)
        max_charger_kw = float(row.max_charger_kw)

        if max_charger_kw <= 0:
            exception_records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="fleet_data",
                    entity_id=vehicle_id,
                    message="Invalid charger power for baseline schedule.",
                    suggested_action="Set max_charger_kw to a positive value.",
                )
            )
            continue

        intervals, interval_exceptions = build_charging_window_intervals(
            arrival_time=row.arrival_time,
            departure_time=row.departure_time,
            run_id=run_id,
            entity_id=vehicle_id,
        )
        exception_records.extend(interval_exceptions.to_dict("records"))

        if required_kwh <= 0:
            if not intervals.empty:
                first_interval = intervals.iloc[0]
                records.append(
                    _schedule_record(
                        row=row,
                        interval=first_interval,
                        run_id=run_id,
                        charge_kw=0.0,
                        charge_kwh=0.0,
                        cumulative_charge_kwh=0.0,
                        required_kwh=required_kwh,
                        remaining_kwh_after_interval=0.0,
                        feasibility_flag="no_energy_required",
                        notes="No additional charging required.",
                    )
                )
            continue

        if intervals.empty:
            exception_records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="fleet_data",
                    entity_id=vehicle_id,
                    message="Vehicle cannot charge because no valid intervals are available.",
                    suggested_action="Review vehicle arrival/departure times.",
                )
            )
            continue

        remaining_kwh = required_kwh
        cumulative_kwh = 0.0
        interval_capacity_kwh = max_charger_kw * 0.5 * efficiency

        for interval in intervals.itertuples(index=False):
            if remaining_kwh <= 1e-9:
                break
            charge_kwh = min(interval_capacity_kwh, remaining_kwh)
            charge_kw = charge_kwh / float(interval.interval_hours) / efficiency
            cumulative_kwh += charge_kwh
            remaining_kwh = max(required_kwh - cumulative_kwh, 0.0)
            records.append(
                _schedule_record(
                    row=row,
                    interval=interval,
                    run_id=run_id,
                    charge_kw=charge_kw,
                    charge_kwh=charge_kwh,
                    cumulative_charge_kwh=cumulative_kwh,
                    required_kwh=required_kwh,
                    remaining_kwh_after_interval=remaining_kwh,
                    feasibility_flag="feasible" if remaining_kwh <= 1e-9 else "in_progress",
                    notes="Immediate-charge baseline interval.",
                )
            )

        if remaining_kwh > 1e-6:
            exception_records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="fleet_data",
                    entity_id=vehicle_id,
                    message="Vehicle baseline schedule delivers less energy than required.",
                    suggested_action="Review charger power, charging window, or target SoC.",
                )
            )
            for record in records:
                if record["vehicle_id"] == vehicle_id:
                    record["feasibility_flag"] = "infeasible"
                    record["notes"] = "Immediate charging cannot meet target before departure."

    schedule = pd.DataFrame.from_records(
        records,
        columns=[
            "run_id",
            "service_date",
            "depot_id",
            "vehicle_id",
            "assigned_charger_id",
            "timestamp",
            "settlement_date",
            "settlement_period",
            "interval_hours",
            "charge_kw",
            "charge_kwh",
            "cumulative_charge_kwh",
            "required_kwh",
            "remaining_kwh_after_interval",
            "baseline_strategy",
            "feasibility_flag",
            "notes",
        ],
    )
    return schedule, exceptions_frame(exception_records)


def aggregate_depot_load(
    vehicle_schedule: pd.DataFrame,
    *,
    run_id: str = "phase3_baseline",
) -> pd.DataFrame:
    """Aggregate vehicle-level baseline schedule to depot half-hourly load."""

    if vehicle_schedule.empty:
        return pd.DataFrame(
            columns=[
                "run_id",
                "timestamp",
                "settlement_date",
                "settlement_period",
                "depot_id",
                "total_charge_kwh",
                "total_charge_mwh",
                "average_charge_kw",
                "interval_kw",
                "active_vehicle_count",
                "charger_count_used",
            ]
        )

    active = vehicle_schedule[vehicle_schedule["charge_kwh"] > 0].copy()
    grouped = (
        active.groupby(
            ["timestamp", "settlement_date", "settlement_period", "depot_id"], dropna=False
        )
        .agg(
            total_charge_kwh=("charge_kwh", "sum"),
            active_vehicle_count=("vehicle_id", "nunique"),
            charger_count_used=("assigned_charger_id", "nunique"),
        )
        .reset_index()
    )
    grouped["run_id"] = run_id
    grouped["total_charge_mwh"] = grouped["total_charge_kwh"] / 1000.0
    grouped["interval_kw"] = grouped["total_charge_kwh"] / 0.5
    grouped["average_charge_kw"] = grouped["interval_kw"]
    return grouped[
        [
            "run_id",
            "timestamp",
            "settlement_date",
            "settlement_period",
            "depot_id",
            "total_charge_kwh",
            "total_charge_mwh",
            "average_charge_kw",
            "interval_kw",
            "active_vehicle_count",
            "charger_count_used",
        ]
    ]


def _schedule_record(
    *,
    row: object,
    interval: object,
    run_id: str,
    charge_kw: float,
    charge_kwh: float,
    cumulative_charge_kwh: float,
    required_kwh: float,
    remaining_kwh_after_interval: float,
    feasibility_flag: str,
    notes: str,
) -> dict[str, object]:
    interval_get = (
        interval.get if isinstance(interval, pd.Series) else lambda name: getattr(interval, name)
    )
    return {
        "run_id": run_id,
        "service_date": row.service_date,
        "depot_id": row.depot_id,
        "vehicle_id": row.vehicle_id,
        "assigned_charger_id": row.assigned_charger_id,
        "timestamp": interval_get("timestamp"),
        "settlement_date": interval_get("settlement_date"),
        "settlement_period": int(interval_get("settlement_period")),
        "interval_hours": float(interval_get("interval_hours")),
        "charge_kw": round(float(charge_kw), 6),
        "charge_kwh": round(float(charge_kwh), 6),
        "cumulative_charge_kwh": round(float(cumulative_charge_kwh), 6),
        "required_kwh": round(float(required_kwh), 6),
        "remaining_kwh_after_interval": round(float(remaining_kwh_after_interval), 6),
        "baseline_strategy": BASELINE_STRATEGY,
        "feasibility_flag": feasibility_flag,
        "notes": notes,
    }
