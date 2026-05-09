"""Linear smart-charging optimizer."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from ev_flex_trading.fleet.charging_windows import build_charging_window_intervals
from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.optimisation.constraints import (
    DEFAULT_SOLVER_TOLERANCE,
    DEFAULT_UNMET_ENERGY_PENALTY_GBP_PER_MWH,
    OPTIMIZED_STRATEGY,
)
from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception


def optimize_smart_charging(
    fleet_requirements: pd.DataFrame,
    market_prices: pd.DataFrame,
    *,
    run_id: str = "phase4_optimization",
    service_date: str | None = None,
    depot_id: str | None = None,
    efficiency: float = 1.0,
    site_import_limit_kw: float | None = None,
    unmet_energy_penalty_gbp_per_mwh: float = DEFAULT_UNMET_ENERGY_PENALTY_GBP_PER_MWH,
    market: str | None = None,
    source: str | None = None,
    price_type: str | None = None,
    tolerance: float = DEFAULT_SOLVER_TOLERANCE,
    include_zero_charge_rows: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Optimize fleet charging cost with linear programming and slack variables."""

    if efficiency <= 0 or efficiency > 1:
        raise ValueError("efficiency must be > 0 and <= 1")
    if site_import_limit_kw is not None and site_import_limit_kw <= 0:
        raise ValueError("site_import_limit_kw must be positive when provided")

    requirements = (
        fleet_requirements.copy()
        if "required_kwh" in fleet_requirements.columns
        else calculate_fleet_requirements(fleet_requirements)
    )
    if depot_id is not None:
        requirements = requirements[requirements["depot_id"].eq(depot_id)].copy()

    prices = _prepare_prices(
        market_prices,
        market=market,
        source=source,
        price_type=price_type,
    )
    now = datetime.now(timezone.utc)
    exception_records = []
    variable_meta = []
    vehicle_ids = []
    vehicle_required = {}
    vehicle_depots = {}
    vehicle_chargers = {}
    vehicle_service_dates = {}

    for row in requirements.itertuples(index=False):
        vehicle_id = row.vehicle_id
        vehicle_ids.append(vehicle_id)
        required_kwh = max(float(row.required_kwh), 0.0)
        vehicle_required[vehicle_id] = required_kwh
        vehicle_depots[vehicle_id] = row.depot_id
        vehicle_chargers[vehicle_id] = row.assigned_charger_id
        vehicle_service_dates[vehicle_id] = row.service_date
        max_charger_kw = float(row.max_charger_kw)

        if max_charger_kw <= 0:
            exception_records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="optimization",
                    entity_id=vehicle_id,
                    message="Invalid charger power for optimization.",
                    suggested_action="Set max_charger_kw to a positive value.",
                )
            )
            continue

        intervals, window_exceptions = build_charging_window_intervals(
            arrival_time=row.arrival_time,
            departure_time=row.departure_time,
            run_id=run_id,
            entity_id=vehicle_id,
        )
        exception_records.extend(window_exceptions.to_dict("records"))
        if intervals.empty and required_kwh > tolerance:
            exception_records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="optimization",
                    entity_id=vehicle_id,
                    message="Vehicle has no valid charging windows for optimization.",
                    suggested_action="Review arrival/departure times or allow partial intervals.",
                )
            )

        for interval in intervals.itertuples(index=False):
            price_key = (str(interval.settlement_date), int(interval.settlement_period))
            price_record = prices.get(price_key)
            if price_record is None:
                exception_records.append(
                    make_exception(
                        run_id=run_id,
                        timestamp=now,
                        severity="high",
                        category="market_data",
                        entity_id=f"{vehicle_id}:SP{interval.settlement_period}",
                        message="Missing market price for valid optimization interval.",
                        suggested_action="Provide complete market prices for all charging intervals.",
                    )
                )
                continue
            variable_meta.append(
                {
                    "vehicle_id": vehicle_id,
                    "depot_id": row.depot_id,
                    "assigned_charger_id": row.assigned_charger_id,
                    "service_date": row.service_date,
                    "timestamp": interval.timestamp,
                    "settlement_date": str(interval.settlement_date),
                    "settlement_period": int(interval.settlement_period),
                    "interval_hours": float(interval.interval_hours),
                    "max_kwh": max_charger_kw * float(interval.interval_hours) * efficiency,
                    "price_gbp_per_mwh": float(price_record["price_gbp_per_mwh"]),
                    "market": price_record.get("market", "selected_market"),
                    "source": price_record.get("source", "selected_source"),
                    "price_type": price_record.get("price_type", "selected_price"),
                    "data_quality_flag": price_record.get("data_quality_flag", "ok"),
                }
            )

    n_charge = len(variable_meta)
    n_slack = len(vehicle_ids)
    if n_charge == 0 and n_slack == 0:
        return (
            _empty_outputs(run_id),
            _empty_depot(run_id),
            _empty_cost(run_id),
            exceptions_frame(exception_records),
        )

    c = np.zeros(n_charge + n_slack)
    bounds = []
    for i, meta in enumerate(variable_meta):
        c[i] = meta["price_gbp_per_mwh"] / 1000.0
        bounds.append((0.0, meta["max_kwh"]))
    for j, vehicle_id in enumerate(vehicle_ids):
        c[n_charge + j] = unmet_energy_penalty_gbp_per_mwh / 1000.0
        bounds.append((0.0, None))

    a_ub = []
    b_ub = []
    for j, vehicle_id in enumerate(vehicle_ids):
        row = np.zeros(n_charge + n_slack)
        for i, meta in enumerate(variable_meta):
            if meta["vehicle_id"] == vehicle_id:
                row[i] = -1.0
        row[n_charge + j] = -1.0
        a_ub.append(row)
        b_ub.append(-vehicle_required[vehicle_id])

    if site_import_limit_kw is not None:
        interval_keys = sorted(
            {(meta["settlement_date"], meta["settlement_period"]) for meta in variable_meta}
        )
        for interval_key in interval_keys:
            row = np.zeros(n_charge + n_slack)
            for i, meta in enumerate(variable_meta):
                if (meta["settlement_date"], meta["settlement_period"]) == interval_key:
                    row[i] = 1.0
            a_ub.append(row)
            b_ub.append(site_import_limit_kw * 0.5)

    result = linprog(
        c,
        A_ub=np.array(a_ub) if a_ub else None,
        b_ub=np.array(b_ub) if b_ub else None,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        exception_records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="critical",
                category="optimization",
                entity_id="solver",
                message=f"Optimizer failed: {result.message}",
                suggested_action="Review constraints, input data, or solver configuration.",
            )
        )
        return (
            _empty_outputs(run_id),
            _empty_depot(run_id),
            _empty_cost(run_id),
            exceptions_frame(exception_records),
        )

    solution = np.where(np.abs(result.x) < tolerance, 0.0, result.x)
    charge_values = solution[:n_charge]
    unmet_values = solution[n_charge:]
    unmet_by_vehicle = {
        vehicle_id: max(float(unmet_values[j]), 0.0) for j, vehicle_id in enumerate(vehicle_ids)
    }
    records = []
    cumulative = {vehicle_id: 0.0 for vehicle_id in vehicle_ids}

    for meta, charge_kwh in zip(variable_meta, charge_values, strict=False):
        charge_kwh = max(float(charge_kwh), 0.0)
        if charge_kwh <= tolerance and not include_zero_charge_rows:
            continue
        vehicle_id = meta["vehicle_id"]
        cumulative[vehicle_id] += charge_kwh
        remaining = max(vehicle_required[vehicle_id] - cumulative[vehicle_id], 0.0)
        unmet_kwh = unmet_by_vehicle[vehicle_id]
        records.append(
            {
                "run_id": run_id,
                "service_date": meta["service_date"],
                "depot_id": meta["depot_id"],
                "vehicle_id": vehicle_id,
                "assigned_charger_id": meta["assigned_charger_id"],
                "timestamp": meta["timestamp"],
                "settlement_date": meta["settlement_date"],
                "settlement_period": meta["settlement_period"],
                "interval_hours": meta["interval_hours"],
                "charge_kw": charge_kwh / meta["interval_hours"] / efficiency,
                "charge_kwh": charge_kwh,
                "cumulative_charge_kwh": cumulative[vehicle_id],
                "required_kwh": vehicle_required[vehicle_id],
                "remaining_kwh_after_interval": remaining,
                "optimized_strategy": OPTIMIZED_STRATEGY,
                "price_gbp_per_mwh": meta["price_gbp_per_mwh"],
                "market": meta["market"],
                "source": meta["source"],
                "price_type": meta["price_type"],
                "data_quality_flag": meta["data_quality_flag"],
                "interval_cost_gbp": charge_kwh / 1000.0 * meta["price_gbp_per_mwh"],
                "feasibility_flag": "undercharged" if unmet_kwh > tolerance else "feasible",
                "unmet_kwh": unmet_kwh,
                "notes": "Price-optimized charging interval.",
            }
        )

    for vehicle_id, unmet_kwh in unmet_by_vehicle.items():
        if unmet_kwh > tolerance:
            exception_records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="optimization",
                    entity_id=vehicle_id,
                    message="Vehicle has unmet energy after optimization.",
                    suggested_action="Review site import cap, charging window, charger power, or target SoC.",
                )
            )

    schedule = pd.DataFrame.from_records(records, columns=_schedule_columns())
    depot_load = aggregate_optimized_depot_load(
        schedule,
        run_id=run_id,
        site_import_limit_kw=site_import_limit_kw,
    )
    cost = optimized_cost_by_interval(depot_load, run_id=run_id)
    return schedule, depot_load, cost, exceptions_frame(exception_records)


def aggregate_optimized_depot_load(
    vehicle_schedule: pd.DataFrame,
    *,
    run_id: str,
    site_import_limit_kw: float | None,
) -> pd.DataFrame:
    """Aggregate optimized vehicle schedule to depot half-hourly load."""

    columns = [
        "run_id",
        "timestamp",
        "settlement_date",
        "settlement_period",
        "depot_id",
        "total_charge_kwh",
        "total_charge_mwh",
        "interval_kw",
        "active_vehicle_count",
        "charger_count_used",
        "site_import_limit_kw",
        "import_limit_utilization_pct",
        "price_gbp_per_mwh",
        "market",
        "source",
        "price_type",
        "data_quality_flag",
        "interval_cost_gbp",
    ]
    if vehicle_schedule.empty:
        return pd.DataFrame(columns=columns)

    active = vehicle_schedule[vehicle_schedule["charge_kwh"] > DEFAULT_SOLVER_TOLERANCE].copy()
    grouped = (
        active.groupby(
            ["timestamp", "settlement_date", "settlement_period", "depot_id"],
            dropna=False,
        )
        .agg(
            total_charge_kwh=("charge_kwh", "sum"),
            active_vehicle_count=("vehicle_id", "nunique"),
            charger_count_used=("assigned_charger_id", "nunique"),
            price_gbp_per_mwh=("price_gbp_per_mwh", "first"),
            market=("market", "first"),
            source=("source", "first"),
            price_type=("price_type", "first"),
            data_quality_flag=("data_quality_flag", "first"),
            interval_cost_gbp=("interval_cost_gbp", "sum"),
        )
        .reset_index()
    )
    grouped["run_id"] = run_id
    grouped["total_charge_mwh"] = grouped["total_charge_kwh"] / 1000.0
    grouped["interval_kw"] = grouped["total_charge_kwh"] / 0.5
    grouped["site_import_limit_kw"] = site_import_limit_kw
    grouped["import_limit_utilization_pct"] = (
        grouped["interval_kw"] / site_import_limit_kw * 100.0 if site_import_limit_kw else pd.NA
    )
    return grouped[columns]


def optimized_cost_by_interval(
    optimized_depot_load: pd.DataFrame,
    *,
    run_id: str,
) -> pd.DataFrame:
    """Return interval-level optimized charging cost."""

    columns = [
        "run_id",
        "timestamp",
        "settlement_date",
        "settlement_period",
        "depot_id",
        "total_charge_mwh",
        "price_gbp_per_mwh",
        "market",
        "source",
        "price_type",
        "data_quality_flag",
        "interval_cost_gbp",
    ]
    if optimized_depot_load.empty:
        return pd.DataFrame(columns=columns)
    result = optimized_depot_load.copy()
    result["run_id"] = run_id
    for column, default in {
        "market": "selected_market",
        "source": "selected_source",
        "price_type": "selected_price",
        "data_quality_flag": "ok",
    }.items():
        if column not in result.columns:
            result[column] = default
    return result[columns]


def _prepare_prices(
    market_prices: pd.DataFrame,
    *,
    market: str | None,
    source: str | None,
    price_type: str | None,
) -> dict[tuple[str, int], dict[str, object]]:
    prices = market_prices.copy()
    prices["settlement_date"] = prices["settlement_date"].astype(str)
    if market is not None and "market" in prices.columns:
        prices = prices[prices["market"].eq(market)]
    if source is not None and "source" in prices.columns:
        prices = prices[prices["source"].eq(source)]
    if price_type is not None and "price_type" in prices.columns:
        prices = prices[prices["price_type"].eq(price_type)]
    prices = prices.drop_duplicates(["settlement_date", "settlement_period"], keep="first")
    return {
        (str(row.settlement_date), int(row.settlement_period)): row._asdict()
        for row in prices.itertuples(index=False)
    }


def _schedule_columns() -> list[str]:
    return [
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
        "optimized_strategy",
        "price_gbp_per_mwh",
        "market",
        "source",
        "price_type",
        "data_quality_flag",
        "interval_cost_gbp",
        "feasibility_flag",
        "unmet_kwh",
        "notes",
    ]


def _empty_outputs(run_id: str) -> pd.DataFrame:
    return pd.DataFrame(columns=_schedule_columns()).assign(run_id=run_id)


def _empty_depot(run_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "run_id",
            "timestamp",
            "settlement_date",
            "settlement_period",
            "depot_id",
            "total_charge_kwh",
            "total_charge_mwh",
            "interval_kw",
            "active_vehicle_count",
            "charger_count_used",
            "site_import_limit_kw",
            "import_limit_utilization_pct",
            "price_gbp_per_mwh",
            "interval_cost_gbp",
        ]
    ).assign(run_id=run_id)


def _empty_cost(run_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "run_id",
            "timestamp",
            "settlement_date",
            "settlement_period",
            "depot_id",
            "total_charge_mwh",
            "price_gbp_per_mwh",
            "interval_cost_gbp",
            "market",
            "source",
            "price_type",
            "data_quality_flag",
        ]
    ).assign(run_id=run_id)
