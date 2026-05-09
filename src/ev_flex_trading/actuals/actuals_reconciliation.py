"""Forecast/scheduled-vs-actual reconciliation."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception


def reconcile_scheduled_vs_actual(
    scheduled_position: pd.DataFrame,
    actual_charging: pd.DataFrame,
    *,
    run_id: str = "phase5_reconciliation",
    minor_deviation_pct: float = 0.02,
    material_deviation_pct: float = 0.10,
    min_abs_deviation_mwh: float = 0.01,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare scheduled position with synthetic actual metered charging."""

    exceptions = []
    now = datetime.now(timezone.utc)
    actual = actual_charging.copy()
    scheduled = scheduled_position.copy()

    duplicate_mask = actual.duplicated(
        ["settlement_date", "settlement_period", "depot_id", "vehicle_id"],
        keep=False,
    )
    for row in actual[duplicate_mask].itertuples():
        exceptions.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="medium",
                category="meter_data",
                entity_id=f"SP{row.settlement_period}",
                message="Duplicate actual meter interval before aggregation.",
                suggested_action="Aggregate or deduplicate vehicle meter records before final reporting.",
            )
        )

    actual["actual_charge_kwh_for_sum"] = actual["actual_charge_kwh"].where(
        actual["meter_quality_flag"].ne("missing")
    )
    actual_agg = (
        actual.groupby(
            ["service_date", "depot_id", "timestamp", "settlement_date", "settlement_period"],
            dropna=False,
        )
        .agg(
            actual_kwh=("actual_charge_kwh_for_sum", "sum"),
            missing_meter_count=(
                "meter_quality_flag",
                lambda values: int((values == "missing").sum()),
            ),
            meter_quality_flag=("meter_quality_flag", _quality_flag),
        )
        .reset_index()
    )
    actual_agg["actual_mwh"] = actual_agg["actual_kwh"] / 1000.0
    actual_agg.loc[actual_agg["meter_quality_flag"].eq("missing"), "actual_mwh"] = pd.NA
    actual_agg["actual_kw"] = actual_agg["actual_kwh"] / 0.5
    actual_agg.loc[actual_agg["meter_quality_flag"].eq("missing"), "actual_kw"] = pd.NA

    merged = scheduled.merge(
        actual_agg,
        on=["service_date", "depot_id", "timestamp", "settlement_date", "settlement_period"],
        how="outer",
    )
    merged["scheduled_mwh"] = merged["scheduled_mwh"].fillna(0.0)
    merged["actual_mwh"] = merged["actual_mwh"].where(merged["meter_quality_flag"].ne("missing"))
    merged["deviation_mwh"] = merged["actual_mwh"] - merged["scheduled_mwh"]
    merged["abs_deviation_mwh"] = merged["deviation_mwh"].abs()
    merged["deviation_pct"] = merged["deviation_mwh"] / merged["scheduled_mwh"].where(
        merged["scheduled_mwh"].abs() > 1e-9
    )
    merged["scheduled_kw"] = merged["scheduled_kw"].fillna(0.0)
    merged["actual_kw"] = merged["actual_kw"].where(merged["meter_quality_flag"].ne("missing"))
    merged["meter_quality_flag"] = merged["meter_quality_flag"].fillna("missing")
    merged["reconciliation_status"] = merged.apply(
        lambda row: _status(
            row,
            minor_deviation_pct=minor_deviation_pct,
            material_deviation_pct=material_deviation_pct,
            min_abs_deviation_mwh=min_abs_deviation_mwh,
        ),
        axis=1,
    )
    merged["exception_flag"] = merged["reconciliation_status"].isin(
        ["material_deviation", "missing_actual", "missing_schedule", "invalid_actual"]
    )
    merged["notes"] = "Scheduled-vs-actual reconciliation."
    merged["run_id"] = run_id

    for row in merged[merged["exception_flag"]].itertuples():
        severity = (
            "high"
            if row.reconciliation_status in {"missing_actual", "invalid_actual"}
            else "medium"
        )
        exceptions.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity=severity,
                category="meter_data",
                entity_id=f"SP{row.settlement_period}",
                message=f"Reconciliation status: {row.reconciliation_status}.",
                suggested_action="Review scheduled position, meter data, and operational disruption notes.",
            )
        )

    return (
        merged[
            [
                "run_id",
                "service_date",
                "depot_id",
                "timestamp",
                "settlement_date",
                "settlement_period",
                "scheduled_mwh",
                "actual_mwh",
                "deviation_mwh",
                "deviation_pct",
                "abs_deviation_mwh",
                "scheduled_kw",
                "actual_kw",
                "meter_quality_flag",
                "reconciliation_status",
                "exception_flag",
                "notes",
            ]
        ],
        exceptions_frame(exceptions),
    )


def _quality_flag(values: pd.Series) -> str:
    if (values == "missing").any():
        return "missing"
    if (values != "ok").any():
        return "review"
    return "ok"


def _status(
    row: pd.Series,
    *,
    minor_deviation_pct: float,
    material_deviation_pct: float,
    min_abs_deviation_mwh: float,
) -> str:
    if pd.isna(row["actual_mwh"]):
        return "missing_actual"
    if row["actual_mwh"] < -1e-9:
        return "invalid_actual"
    if row["scheduled_mwh"] <= 1e-9 and row["actual_mwh"] > 1e-9:
        return "missing_schedule"
    abs_dev = abs(float(row["deviation_mwh"]))
    pct = abs(float(row["deviation_pct"])) if pd.notna(row["deviation_pct"]) else 0.0
    if abs_dev >= min_abs_deviation_mwh and pct >= material_deviation_pct:
        return "material_deviation"
    if pct >= minor_deviation_pct or abs_dev > 1e-9:
        return "minor_deviation"
    return "matched"
