"""Reusable data quality checks returning structured exceptions."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.utils.settlement_periods import validate_half_hourly_coverage
from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception
from ev_flex_trading.validation.schemas import (
    DataFrameSchema,
    FLEET_SCHEDULE_SCHEMA,
    MARKET_PRICE_SCHEMA,
)


def validate_schema(
    frame: pd.DataFrame,
    schema: DataFrameSchema,
    *,
    run_id: str,
    category: str,
) -> pd.DataFrame:
    records = []
    now = datetime.now(timezone.utc)

    missing_columns = [column for column in schema.required_columns if column not in frame.columns]
    for column in missing_columns:
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="critical",
                category=category,
                entity_id=column,
                message=f"Missing required column: {column}",
                suggested_action="Add the required column or correct the input mapping.",
            )
        )

    if missing_columns:
        return exceptions_frame(records)

    for column in schema.columns:
        if not column.required or column.name not in frame.columns:
            continue
        null_mask = frame[column.name].isna()
        for idx in frame.index[null_mask]:
            records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category=category,
                    entity_id=idx,
                    message=f"Null required field: {column.name}",
                    suggested_action="Review source data and populate required values.",
                )
            )
        if column.validator is not None:
            valid_mask = column.validator(frame[column.name]).fillna(False)
            for idx in frame.index[~valid_mask]:
                records.append(
                    make_exception(
                        run_id=run_id,
                        timestamp=now,
                        severity="high",
                        category=category,
                        entity_id=idx,
                        message=f"{column.name}: {column.message}",
                        suggested_action="Review and correct the invalid source value.",
                    )
                )

    return exceptions_frame(records)


def check_fleet_schedule_quality(
    frame: pd.DataFrame,
    *,
    run_id: str = "phase1",
) -> pd.DataFrame:
    records = validate_schema(
        frame,
        FLEET_SCHEDULE_SCHEMA,
        run_id=run_id,
        category="fleet_data",
    ).to_dict("records")

    required = set(FLEET_SCHEDULE_SCHEMA.required_columns)
    if not required.issubset(frame.columns):
        return exceptions_frame(records)

    now = datetime.now(timezone.utc)
    duplicate_mask = frame.duplicated(["service_date", "depot_id", "vehicle_id"], keep=False)
    for row in frame[duplicate_mask].itertuples():
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="high",
                category="fleet_data",
                entity_id=getattr(row, "vehicle_id", row.Index),
                message="Duplicate vehicle_id for service_date and depot_id.",
                suggested_action="Ensure each vehicle appears once per depot service day.",
            )
        )

    start_soc = pd.to_numeric(frame["start_soc_pct"], errors="coerce")
    target_soc = pd.to_numeric(frame["target_soc_pct"], errors="coerce")
    target_below_start = target_soc < start_soc
    for row in frame[target_below_start].itertuples():
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="medium",
                category="fleet_data",
                entity_id=getattr(row, "vehicle_id", row.Index),
                message="target_soc_pct is below start_soc_pct.",
                suggested_action="Confirm whether no charging is required or correct the SoC inputs.",
            )
        )

    try:
        requirements = calculate_fleet_requirements(frame)
        infeasible = requirements["feasibility_flag"].eq("infeasible")
        for row in requirements[infeasible].itertuples():
            records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="fleet_data",
                    entity_id=row.vehicle_id,
                    message=row.feasibility_message,
                    suggested_action="Review charger power, arrival/departure times, or target SoC.",
                )
            )
    except Exception as exc:  # pragma: no cover - defensive conversion to structured exception.
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="critical",
                category="fleet_data",
                entity_id="fleet_requirements",
                message=f"Could not calculate fleet requirements: {exc}",
                suggested_action="Fix blocking fleet schedule validation errors first.",
            )
        )

    return exceptions_frame(records)


def check_market_price_quality(
    frame: pd.DataFrame,
    *,
    service_date: str,
    run_id: str = "phase1",
) -> pd.DataFrame:
    records = validate_schema(
        frame,
        MARKET_PRICE_SCHEMA,
        run_id=run_id,
        category="market_data",
    ).to_dict("records")
    now = datetime.now(timezone.utc)

    required = set(MARKET_PRICE_SCHEMA.required_columns)
    if not required.issubset(frame.columns):
        return exceptions_frame(records)

    if "settlement_period" in frame.columns:
        coverage = validate_half_hourly_coverage(frame, service_date)
        for period in coverage["missing_periods"]:
            records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="market_data",
                    entity_id=period,
                    message="Missing half-hourly market interval.",
                    suggested_action="Reload source data or apply a documented estimate.",
                )
            )
        for period in coverage["duplicate_periods"]:
            records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="medium",
                    category="market_data",
                    entity_id=period,
                    message="Duplicate settlement period in market data.",
                    suggested_action="Deduplicate market intervals before downstream calculations.",
                )
            )

    expected_periods = set(
        validate_half_hourly_coverage(frame.iloc[0:0], service_date)["missing_periods"]
    )
    numeric_periods = pd.to_numeric(frame["settlement_period"], errors="coerce")
    invalid_periods = ~numeric_periods.isin(expected_periods)
    for row in frame[invalid_periods].itertuples():
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="high",
                category="market_data",
                entity_id=getattr(row, "settlement_period", row.Index),
                message="Settlement period is invalid for the service date.",
                suggested_action="Check settlement-period mapping and source timestamp.",
            )
        )

    duplicate_subset = ["settlement_date", "settlement_period", "market", "source"]
    duplicate_mask = frame.duplicated(duplicate_subset, keep=False)
    for row in frame[duplicate_mask].itertuples():
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="medium",
                category="market_data",
                entity_id=f"{row.source}:{row.market}:SP{row.settlement_period}",
                message="Duplicate market price record for settlement period, market, and source.",
                suggested_action="Deduplicate market price records before downstream calculations.",
            )
        )

    prices = pd.to_numeric(frame["price_gbp_per_mwh"], errors="coerce")
    implausible = prices.abs() > 1000
    for row in frame[implausible].itertuples():
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="medium",
                category="market_data",
                entity_id=f"SP{row.settlement_period}",
                message="Implausible market price magnitude above 1000 GBP/MWh.",
                suggested_action="Confirm whether this is a genuine price spike or a unit issue.",
            )
        )

    if "currency" in frame.columns and frame["currency"].dropna().nunique() > 1:
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="high",
                category="market_data",
                entity_id="currency",
                message="Mixed currencies detected in market price data.",
                suggested_action="Convert all prices to GBP before downstream use.",
            )
        )

    if "unit" in frame.columns and frame["unit"].dropna().nunique() > 1:
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="high",
                category="market_data",
                entity_id="unit",
                message="Mixed price units detected in market price data.",
                suggested_action="Convert all prices to GBP/MWh before downstream use.",
            )
        )

    return exceptions_frame(records)
