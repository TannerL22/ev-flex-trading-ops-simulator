"""Synthetic actual charging data generation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_actual_charging(
    optimized_vehicle_schedule: pd.DataFrame,
    *,
    run_id: str = "phase5_actuals",
    random_seed: int = 42,
    scenario: str = "base_actuals",
) -> pd.DataFrame:
    """Generate synthetic actual metered charging from an optimized schedule.

    The simulator is intentionally simple and transparent. It preserves scheduled
    intervals, then applies scenario-specific deviations for testing operational
    reconciliation workflows.
    """

    rng = np.random.default_rng(random_seed)
    frame = optimized_vehicle_schedule.copy()
    if frame.empty:
        return _empty_actuals()

    frame["scheduled_charge_kwh"] = pd.to_numeric(frame["charge_kwh"], errors="coerce").fillna(0.0)
    frame["actual_charge_kwh"] = frame["scheduled_charge_kwh"].astype(float)
    frame["meter_quality_flag"] = "ok"
    frame["actuals_scenario"] = scenario
    frame["disruption_type"] = "none"
    frame["notes"] = "Synthetic actual follows optimized schedule."

    noise_scale = 0.015 if scenario == "base_actuals" else 0.04
    noise = rng.normal(1.0, noise_scale, len(frame))
    frame["actual_charge_kwh"] = frame["actual_charge_kwh"] * noise

    if scenario in {"late_arrivals", "high_deviation"}:
        _apply_late_arrivals(
            frame, rng, vehicle_fraction=0.25 if scenario == "late_arrivals" else 0.35
        )

    if scenario in {"charger_derating", "high_deviation"}:
        _apply_derating(
            frame, rng, vehicle_fraction=0.25 if scenario == "charger_derating" else 0.35
        )

    if scenario == "missing_meter_data":
        _apply_missing_meter_data(frame, rng, row_fraction=0.12)
    elif scenario == "high_deviation":
        _apply_missing_meter_data(frame, rng, row_fraction=0.06)

    if scenario == "high_deviation":
        boost_mask = rng.random(len(frame)) < 0.12
        frame.loc[boost_mask, "actual_charge_kwh"] *= 1.12
        frame.loc[boost_mask, "disruption_type"] = frame.loc[boost_mask, "disruption_type"].mask(
            frame.loc[boost_mask, "disruption_type"].eq("none"),
            "extra_energy_noise",
        )

    max_physical_kwh = pd.to_numeric(frame["charge_kw"], errors="coerce").fillna(0.0) * 0.5 * 1.15
    frame["actual_charge_kwh"] = frame["actual_charge_kwh"].clip(lower=0.0, upper=max_physical_kwh)
    frame.loc[frame["actual_charge_kwh"].isna(), "meter_quality_flag"] = "missing"
    frame["actual_charge_kw"] = frame["actual_charge_kwh"] / pd.to_numeric(
        frame["interval_hours"], errors="coerce"
    )

    result = frame[
        [
            "run_id",
            "service_date",
            "depot_id",
            "vehicle_id",
            "assigned_charger_id",
            "timestamp",
            "settlement_date",
            "settlement_period",
            "scheduled_charge_kwh",
            "actual_charge_kwh",
            "actual_charge_kw",
            "meter_quality_flag",
            "actuals_scenario",
            "disruption_type",
            "notes",
        ]
    ].copy()
    result["run_id"] = run_id
    return result


def _apply_late_arrivals(
    frame: pd.DataFrame, rng: np.random.Generator, *, vehicle_fraction: float
) -> None:
    vehicles = np.array(sorted(frame["vehicle_id"].unique()))
    if len(vehicles) == 0:
        return
    selected = set(
        rng.choice(vehicles, size=max(1, int(len(vehicles) * vehicle_fraction)), replace=False)
    )
    for vehicle_id in selected:
        vehicle_idx = frame.index[frame["vehicle_id"].eq(vehicle_id)].tolist()
        if len(vehicle_idx) <= 1:
            continue
        first = vehicle_idx[0]
        moved_energy = frame.loc[first, "actual_charge_kwh"] * 0.75
        frame.loc[first, "actual_charge_kwh"] -= moved_energy
        frame.loc[vehicle_idx[1], "actual_charge_kwh"] += moved_energy
        frame.loc[[first, vehicle_idx[1]], "disruption_type"] = "late_arrival_shift"
        frame.loc[[first, vehicle_idx[1]], "notes"] = (
            "Synthetic late arrival shifted charging later."
        )


def _apply_derating(
    frame: pd.DataFrame, rng: np.random.Generator, *, vehicle_fraction: float
) -> None:
    vehicles = np.array(sorted(frame["vehicle_id"].unique()))
    if len(vehicles) == 0:
        return
    selected = set(
        rng.choice(vehicles, size=max(1, int(len(vehicles) * vehicle_fraction)), replace=False)
    )
    mask = frame["vehicle_id"].isin(selected)
    frame.loc[mask, "actual_charge_kwh"] *= 0.72
    frame.loc[mask, "disruption_type"] = "charger_derating"
    frame.loc[mask, "notes"] = "Synthetic charger derating reduced metered charging."


def _apply_missing_meter_data(
    frame: pd.DataFrame, rng: np.random.Generator, *, row_fraction: float
) -> None:
    if frame.empty:
        return
    count = max(1, int(len(frame) * row_fraction))
    selected = rng.choice(frame.index.to_numpy(), size=count, replace=False)
    frame.loc[selected, "actual_charge_kwh"] = pd.NA
    frame.loc[selected, "meter_quality_flag"] = "missing"
    frame.loc[selected, "disruption_type"] = "missing_meter_data"
    frame.loc[selected, "notes"] = "Synthetic missing meter interval."


def _empty_actuals() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "run_id",
            "service_date",
            "depot_id",
            "vehicle_id",
            "assigned_charger_id",
            "timestamp",
            "settlement_date",
            "settlement_period",
            "scheduled_charge_kwh",
            "actual_charge_kwh",
            "actual_charge_kw",
            "meter_quality_flag",
            "actuals_scenario",
            "disruption_type",
            "notes",
        ]
    )
