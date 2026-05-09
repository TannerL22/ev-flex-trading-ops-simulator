"""Compare optimized charging against the dumb baseline."""

from __future__ import annotations

import pandas as pd


def build_optimization_summary(
    *,
    optimized_vehicle_schedule: pd.DataFrame,
    optimized_depot_load: pd.DataFrame,
    optimized_cost_by_interval: pd.DataFrame,
    baseline_vehicle_schedule: pd.DataFrame,
    baseline_depot_load: pd.DataFrame,
    baseline_cost_by_interval: pd.DataFrame,
    run_id: str,
    service_date: str,
    depot_id: str,
    site_import_limit_kw: float | None,
    exception_count: int,
) -> pd.DataFrame:
    """Create one-row baseline-vs-optimized comparison metrics."""

    optimized_delivered_mwh = float(optimized_depot_load["total_charge_mwh"].sum())
    optimized_cost = float(optimized_cost_by_interval["interval_cost_gbp"].sum())
    optimized_wavg = optimized_cost / optimized_delivered_mwh if optimized_delivered_mwh else 0.0
    optimized_peak = (
        float(optimized_depot_load["interval_kw"].max()) if not optimized_depot_load.empty else 0.0
    )

    baseline_delivered_mwh = float(baseline_depot_load["total_charge_mwh"].sum())
    baseline_cost = float(baseline_cost_by_interval["interval_cost_gbp"].sum())
    baseline_wavg = baseline_cost / baseline_delivered_mwh if baseline_delivered_mwh else 0.0
    baseline_peak = (
        float(baseline_depot_load["interval_kw"].max()) if not baseline_depot_load.empty else 0.0
    )

    (
        vehicles_total,
        vehicles_fully_charged,
        vehicles_undercharged,
        total_required_mwh,
        total_unmet_mwh,
    ) = _vehicle_readiness(optimized_vehicle_schedule)
    readiness_pct = (vehicles_fully_charged / vehicles_total * 100.0) if vehicles_total else 0.0
    savings = baseline_cost - optimized_cost
    savings_pct = (savings / baseline_cost * 100.0) if baseline_cost else 0.0
    peak_reduction = baseline_peak - optimized_peak
    peak_reduction_pct = (peak_reduction / baseline_peak * 100.0) if baseline_peak else 0.0

    return pd.DataFrame.from_records(
        [
            {
                "run_id": run_id,
                "service_date": service_date,
                "depot_id": depot_id,
                "vehicles_total": vehicles_total,
                "vehicles_fully_charged": vehicles_fully_charged,
                "vehicles_undercharged": vehicles_undercharged,
                "vehicle_readiness_pct": readiness_pct,
                "total_required_mwh": total_required_mwh,
                "optimized_delivered_mwh": optimized_delivered_mwh,
                "optimized_cost_gbp": optimized_cost,
                "optimized_weighted_avg_price_gbp_per_mwh": optimized_wavg,
                "optimized_peak_import_kw": optimized_peak,
                "baseline_delivered_mwh": baseline_delivered_mwh,
                "baseline_cost_gbp": baseline_cost,
                "baseline_weighted_avg_price_gbp_per_mwh": baseline_wavg,
                "baseline_peak_import_kw": baseline_peak,
                "savings_gbp": savings,
                "savings_pct": savings_pct,
                "peak_reduction_kw": peak_reduction,
                "peak_reduction_pct": peak_reduction_pct,
                "total_unmet_mwh": total_unmet_mwh,
                "site_import_limit_kw": site_import_limit_kw,
                "exception_count": exception_count,
                "materially_shifted_intervals": count_materially_shifted_intervals(
                    baseline_depot_load,
                    optimized_depot_load,
                ),
                "notes": "Optimized charging cost comparison only; not full trading P&L.",
            }
        ]
    )


def count_materially_shifted_intervals(
    baseline_depot_load: pd.DataFrame,
    optimized_depot_load: pd.DataFrame,
    *,
    threshold_kwh: float = 1.0,
) -> int:
    """Count intervals where optimized load differs materially from baseline load."""

    left = baseline_depot_load[["settlement_date", "settlement_period", "total_charge_kwh"]].rename(
        columns={"total_charge_kwh": "baseline_kwh"}
    )
    right = optimized_depot_load[
        ["settlement_date", "settlement_period", "total_charge_kwh"]
    ].rename(columns={"total_charge_kwh": "optimized_kwh"})
    merged = left.merge(right, on=["settlement_date", "settlement_period"], how="outer").fillna(0)
    return int((merged["baseline_kwh"] - merged["optimized_kwh"]).abs().gt(threshold_kwh).sum())


def _vehicle_readiness(schedule: pd.DataFrame) -> tuple[int, int, int, float, float]:
    if schedule.empty:
        return 0, 0, 0, 0.0, 0.0
    latest = schedule.sort_values("timestamp").groupby("vehicle_id", as_index=False).tail(1)
    vehicles_total = int(schedule["vehicle_id"].nunique())
    vehicles_fully_charged = int((latest["unmet_kwh"] <= 1e-6).sum())
    vehicles_undercharged = vehicles_total - vehicles_fully_charged
    total_required_mwh = (
        schedule[["vehicle_id", "required_kwh"]].drop_duplicates()["required_kwh"].sum() / 1000.0
    )
    total_unmet_mwh = latest["unmet_kwh"].sum() / 1000.0
    return (
        vehicles_total,
        vehicles_fully_charged,
        vehicles_undercharged,
        float(total_required_mwh),
        float(total_unmet_mwh),
    )
