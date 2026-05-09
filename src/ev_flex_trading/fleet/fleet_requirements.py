"""Fleet charging requirement calculations."""

from __future__ import annotations

import pandas as pd


def calculate_fleet_requirements(fleet_schedule: pd.DataFrame) -> pd.DataFrame:
    """Add simple vehicle-level charging requirement and feasibility fields."""

    result = fleet_schedule.copy()
    arrival = pd.to_datetime(result["arrival_time"])
    departure = pd.to_datetime(result["departure_time"])

    result["required_kwh"] = (
        pd.to_numeric(result["battery_kwh"])
        * (pd.to_numeric(result["target_soc_pct"]) - pd.to_numeric(result["start_soc_pct"]))
        / 100.0
    ).clip(lower=0)
    result["available_charging_hours"] = (departure - arrival).dt.total_seconds() / 3600.0
    result["min_average_kw_required"] = result["required_kwh"] / result[
        "available_charging_hours"
    ].where(result["available_charging_hours"] > 0)

    max_deliverable_kwh = (
        pd.to_numeric(result["max_charger_kw"]) * result["available_charging_hours"]
    )
    feasible = (result["required_kwh"] <= max_deliverable_kwh) & (
        result["available_charging_hours"] > 0
    )
    no_energy_required = result["required_kwh"].eq(0) & (result["available_charging_hours"] > 0)

    result["feasibility_flag"] = "feasible"
    result.loc[no_energy_required, "feasibility_flag"] = "no_energy_required"
    result.loc[~feasible & ~no_energy_required, "feasibility_flag"] = "infeasible"

    result["feasibility_message"] = "Vehicle can meet target SoC within plug-in window."
    result.loc[no_energy_required, "feasibility_message"] = "No additional charging required."
    result.loc[result["available_charging_hours"] <= 0, "feasibility_message"] = (
        "Departure must be after arrival."
    )
    result.loc[
        (result["available_charging_hours"] > 0) & (result["required_kwh"] > max_deliverable_kwh),
        "feasibility_message",
    ] = "Required energy exceeds what the assigned charger can deliver before departure."

    return result
