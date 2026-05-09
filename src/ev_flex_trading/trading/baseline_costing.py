"""Baseline charging cost calculations."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception


def calculate_baseline_charging_cost(
    depot_load: pd.DataFrame,
    market_prices: pd.DataFrame,
    *,
    vehicle_schedule: pd.DataFrame | None = None,
    market: str | None = None,
    source: str | None = None,
    price_type: str | None = None,
    run_id: str = "phase3_baseline",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Join depot load to market prices and calculate baseline charging cost."""

    exceptions = []
    now = datetime.now(timezone.utc)
    prices = market_prices.copy()
    load = depot_load.copy()
    if "settlement_date" in prices.columns:
        prices["settlement_date"] = prices["settlement_date"].astype(str)
    if "settlement_date" in load.columns:
        load["settlement_date"] = load["settlement_date"].astype(str)
    if market is not None:
        prices = prices[prices["market"].eq(market)]
    if source is not None:
        prices = prices[prices["source"].eq(source)]
    if price_type is not None and "price_type" in prices.columns:
        prices = prices[prices["price_type"].eq(price_type)]

    duplicate_subset = ["settlement_date", "settlement_period"]
    duplicate_mask = prices.duplicated(duplicate_subset, keep=False)
    if duplicate_mask.any():
        for row in prices[duplicate_mask].itertuples():
            exceptions.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="medium",
                    category="market_data",
                    entity_id=f"SP{row.settlement_period}",
                    message="Duplicate market price interval after filtering.",
                    suggested_action="Filter to one source/market/price_type before costing.",
                )
            )
        prices = prices.drop_duplicates(duplicate_subset, keep="first")

    price_columns = [
        "settlement_date",
        "settlement_period",
        "price_gbp_per_mwh",
        "market",
        "source",
        "price_type",
        "data_quality_flag",
    ]
    available_price_columns = [column for column in price_columns if column in prices.columns]
    cost = load.merge(
        prices[available_price_columns],
        on=["settlement_date", "settlement_period"],
        how="left",
    )
    cost["price_gbp_per_mwh"] = pd.to_numeric(cost["price_gbp_per_mwh"], errors="coerce")
    cost["interval_cost_gbp"] = cost["total_charge_mwh"] * cost["price_gbp_per_mwh"]

    missing_price = cost["price_gbp_per_mwh"].isna()
    for row in cost[missing_price].itertuples():
        exceptions.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="medium",
                category="market_data",
                entity_id=f"SP{row.settlement_period}",
                message="Missing market price for charging interval.",
                suggested_action="Provide a complete market price curve or document an estimate.",
            )
        )

    cost["run_id"] = run_id
    cost = cost[
        [
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
    ]

    summary = summarize_baseline_cost(
        cost,
        depot_load=load,
        vehicle_schedule=vehicle_schedule,
        exception_count=len(exceptions),
        run_id=run_id,
    )
    return cost, summary, exceptions_frame(exceptions)


def summarize_baseline_cost(
    cost_by_interval: pd.DataFrame,
    *,
    depot_load: pd.DataFrame,
    vehicle_schedule: pd.DataFrame | None,
    exception_count: int,
    run_id: str,
) -> pd.DataFrame:
    """Create a one-row baseline charging cost summary."""

    total_delivered_mwh = float(cost_by_interval["total_charge_mwh"].sum())
    total_cost = float(cost_by_interval["interval_cost_gbp"].sum(skipna=True))
    weighted_avg = total_cost / total_delivered_mwh if total_delivered_mwh > 0 else 0.0
    peak_import_kw = float(depot_load["interval_kw"].max()) if not depot_load.empty else 0.0
    depot_id = str(depot_load["depot_id"].iloc[0]) if not depot_load.empty else ""
    service_date = (
        str(cost_by_interval["settlement_date"].iloc[0]) if not cost_by_interval.empty else ""
    )

    vehicles_total = vehicles_fully_charged = vehicles_undercharged = 0
    total_required_mwh = 0.0
    if vehicle_schedule is not None and not vehicle_schedule.empty:
        latest = (
            vehicle_schedule.sort_values("timestamp").groupby("vehicle_id", as_index=False).tail(1)
        )
        vehicles_total = int(vehicle_schedule["vehicle_id"].nunique())
        vehicles_fully_charged = int((latest["remaining_kwh_after_interval"] <= 1e-6).sum())
        vehicles_undercharged = vehicles_total - vehicles_fully_charged
        total_required_mwh = (
            vehicle_schedule[["vehicle_id", "required_kwh"]].drop_duplicates()["required_kwh"].sum()
            / 1000.0
        )

    missing_price_intervals = int(cost_by_interval["price_gbp_per_mwh"].isna().sum())
    readiness_pct = (vehicles_fully_charged / vehicles_total * 100.0) if vehicles_total else 0.0

    return pd.DataFrame.from_records(
        [
            {
                "run_id": run_id,
                "service_date": service_date,
                "depot_id": depot_id,
                "total_required_mwh": total_required_mwh,
                "total_delivered_mwh": total_delivered_mwh,
                "total_baseline_cost_gbp": total_cost,
                "weighted_avg_price_gbp_per_mwh": weighted_avg,
                "peak_import_kw": peak_import_kw,
                "vehicles_total": vehicles_total,
                "vehicles_fully_charged": vehicles_fully_charged,
                "vehicles_undercharged": vehicles_undercharged,
                "vehicle_readiness_pct": readiness_pct,
                "missing_price_intervals": missing_price_intervals,
                "exception_count": exception_count,
                "notes": "Dumb-charging baseline cost only; not full trading P&L.",
            }
        ]
    )
