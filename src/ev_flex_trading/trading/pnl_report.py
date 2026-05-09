"""P&L-style daily summaries for trading support reporting."""

from __future__ import annotations

import pandas as pd


def build_daily_pnl_style_summary(
    settlement_style: pd.DataFrame,
    *,
    baseline_summary: pd.DataFrame,
    optimized_summary: pd.DataFrame,
    reconciliation: pd.DataFrame,
    exceptions: pd.DataFrame,
    run_id: str,
    scenario: str,
) -> pd.DataFrame:
    """Build a one-row P&L-style summary.

    This is not official settlement or real trading P&L. It is a simplified
    trading-support view for comparing planned and actual charging outcomes.
    """

    scheduled_mwh = float(settlement_style["scheduled_mwh"].sum())
    actual_mwh = float(settlement_style["actual_mwh"].sum(skipna=True))
    deviation_mwh = actual_mwh - scheduled_mwh
    abs_deviation_mwh = float(
        settlement_style["deviation_mwh"].fillna(-settlement_style["scheduled_mwh"]).abs().sum()
    )
    scheduled_cost = float(settlement_style["scheduled_cost_gbp"].sum(skipna=True))
    actual_energy_cost = float(settlement_style["actual_energy_cost_gbp"].sum(skipna=True))
    imbalance_exposure = float(settlement_style["imbalance_exposure_gbp"].sum(skipna=True))
    total_cost = float(settlement_style["total_settlement_style_cost_gbp"].sum(skipna=True))

    baseline_cost = float(baseline_summary.iloc[0]["baseline_cost_gbp"])
    optimized_cost = float(optimized_summary.iloc[0]["optimized_cost_gbp"])
    expected_savings = baseline_cost - optimized_cost
    realized_savings = baseline_cost - total_cost
    realized_savings_pct = realized_savings / baseline_cost * 100.0 if baseline_cost else 0.0
    delta_vs_plan = total_cost - optimized_cost

    return pd.DataFrame.from_records(
        [
            {
                "run_id": run_id,
                "service_date": (
                    settlement_style.iloc[0]["service_date"] if not settlement_style.empty else ""
                ),
                "depot_id": (
                    settlement_style.iloc[0]["depot_id"] if not settlement_style.empty else ""
                ),
                "scenario": scenario,
                "vehicles_total": int(optimized_summary.iloc[0]["vehicles_total"]),
                "scheduled_mwh": scheduled_mwh,
                "actual_mwh": actual_mwh,
                "deviation_mwh": deviation_mwh,
                "absolute_deviation_mwh": abs_deviation_mwh,
                "deviation_pct": deviation_mwh / scheduled_mwh if scheduled_mwh else 0.0,
                "scheduled_cost_gbp": scheduled_cost,
                "actual_energy_cost_gbp": actual_energy_cost,
                "imbalance_exposure_gbp": imbalance_exposure,
                "total_settlement_style_cost_gbp": total_cost,
                "dumb_baseline_cost_gbp": baseline_cost,
                "optimized_expected_cost_gbp": optimized_cost,
                "expected_savings_vs_baseline_gbp": expected_savings,
                "realized_savings_vs_baseline_gbp": realized_savings,
                "realized_savings_vs_baseline_pct": realized_savings_pct,
                "delta_vs_optimized_plan_gbp": delta_vs_plan,
                "vehicle_readiness_pct": float(optimized_summary.iloc[0]["vehicle_readiness_pct"]),
                "material_deviation_intervals": int(
                    reconciliation["reconciliation_status"].eq("material_deviation").sum()
                ),
                "missing_meter_intervals": int(
                    reconciliation["reconciliation_status"].eq("missing_actual").sum()
                ),
                "exception_count": len(exceptions),
                "notes": "P&L-style summary from simplified settlement-style simulation.",
            }
        ]
    )
