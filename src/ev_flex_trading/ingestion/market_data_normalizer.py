"""Normalize raw market price inputs to the shared market price schema."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from ev_flex_trading.config import DEFAULT_TIMEZONE
from ev_flex_trading.utils.settlement_periods import (
    generate_settlement_periods,
    timestamp_to_settlement_period,
)
from ev_flex_trading.validation.data_quality_checks import check_market_price_quality
from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception

MARKET_PRICE_COLUMNS = [
    "timestamp",
    "settlement_date",
    "settlement_period",
    "price_gbp_per_mwh",
    "source",
    "market",
    "price_type",
    "currency",
    "unit",
    "ingestion_timestamp",
    "data_quality_flag",
    "notes",
]


def _as_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value) if isinstance(value, str) else value


def _coalesce_column(frame: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for candidate in candidates:
        if candidate in frame.columns:
            return frame[candidate]
    return None


def _timestamp_from_delivery_columns(frame: pd.DataFrame, service_date: date | None) -> pd.Series:
    if "timestamp" in frame.columns:
        return pd.to_datetime(frame["timestamp"], errors="coerce", utc=True).dt.tz_convert(
            DEFAULT_TIMEZONE
        )
    if "delivery_start" in frame.columns:
        return pd.to_datetime(frame["delivery_start"], errors="coerce", utc=True).dt.tz_convert(
            DEFAULT_TIMEZONE
        )
    if {"delivery_date", "settlement_period"}.issubset(frame.columns):
        rows = []
        for raw_date, raw_period in zip(
            frame["delivery_date"], frame["settlement_period"], strict=False
        ):
            try:
                local_date = date.fromisoformat(str(raw_date))
                period = int(raw_period)
                periods = generate_settlement_periods(local_date)
                rows.append(
                    periods.loc[periods["settlement_period"].eq(period), "period_start"].iloc[0]
                )
            except Exception:
                rows.append(pd.NaT)
        return pd.Series(rows, index=frame.index)
    if service_date is not None and "settlement_period" in frame.columns:
        periods = generate_settlement_periods(service_date).set_index("settlement_period")
        return frame["settlement_period"].apply(
            lambda period: (
                periods.loc[int(period), "period_start"] if int(period) in periods.index else pd.NaT
            )
        )
    return pd.Series([pd.NaT] * len(frame), index=frame.index)


def normalize_market_prices(
    raw_frame: pd.DataFrame,
    *,
    service_date: date | str | None = None,
    default_source: str = "unknown",
    default_market: str = "unknown",
    default_price_type: str = "unknown",
    run_id: str = "market_normalization",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize raw price records and return `(normalized, exceptions)`.

    Supported raw formats include:
    - `timestamp`, `price_gbp_per_mwh`, `market`
    - `delivery_date`, `settlement_period`, `price_gbp_per_mwh`, `market`
    - `delivery_start`, `price_gbp_per_mwh`, `market`
    """

    local_service_date = _as_date(service_date)
    frame = raw_frame.copy()
    records: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    price_series = _coalesce_column(frame, ["price_gbp_per_mwh", "price", "system_price"])
    if price_series is None:
        price_series = pd.Series([pd.NA] * len(frame), index=frame.index)
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="critical",
                category="market_data",
                entity_id="price_gbp_per_mwh",
                message="Missing required price column.",
                suggested_action="Provide price_gbp_per_mwh or map the source price field.",
            )
        )

    normalized = pd.DataFrame(index=frame.index)
    normalized["timestamp"] = _timestamp_from_delivery_columns(frame, local_service_date)
    normalized["price_gbp_per_mwh"] = pd.to_numeric(price_series, errors="coerce")
    normalized["source"] = (
        frame["source"].fillna(default_source) if "source" in frame.columns else default_source
    )
    normalized["market"] = (
        frame["market"].fillna(default_market) if "market" in frame.columns else default_market
    )
    normalized["price_type"] = (
        frame["price_type"].fillna(default_price_type)
        if "price_type" in frame.columns
        else default_price_type
    )
    normalized["currency"] = (
        frame["currency"].fillna("GBP") if "currency" in frame.columns else "GBP"
    )
    normalized["unit"] = frame["unit"].fillna("MWh") if "unit" in frame.columns else "MWh"
    normalized["ingestion_timestamp"] = now.isoformat()
    normalized["data_quality_flag"] = "ok"
    normalized["notes"] = frame["notes"].fillna("") if "notes" in frame.columns else ""

    settlement_records = []
    for idx, timestamp in normalized["timestamp"].items():
        if pd.isna(timestamp):
            records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="market_data",
                    entity_id=idx,
                    message="Timestamp could not be parsed for market price row.",
                    suggested_action="Check timestamp, delivery_start, or delivery_date/settlement_period fields.",
                )
            )
            settlement_records.append((pd.NA, pd.NA))
            continue
        mapped = timestamp_to_settlement_period(pd.Timestamp(timestamp).to_pydatetime())
        settlement_records.append((mapped.settlement_date, mapped.settlement_period))

    normalized["settlement_date"] = [record[0] for record in settlement_records]
    normalized["settlement_period"] = [record[1] for record in settlement_records]

    normalized = normalized[MARKET_PRICE_COLUMNS]

    if local_service_date is None:
        valid_dates = normalized["settlement_date"].dropna()
        if not valid_dates.empty:
            local_service_date = valid_dates.iloc[0]

    if local_service_date is not None:
        quality = check_market_price_quality(
            normalized,
            service_date=local_service_date.isoformat(),
            run_id=run_id,
        )
        records.extend(quality.to_dict("records"))

    invalid_price_rows = normalized["price_gbp_per_mwh"].isna()
    for idx in normalized.index[invalid_price_rows]:
        records.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="high",
                category="market_data",
                entity_id=idx,
                message="Market price is missing or non-numeric.",
                suggested_action="Correct the source price value before using it downstream.",
            )
        )

    if records:
        normalized.loc[:, "data_quality_flag"] = "review"

    return normalized.reset_index(drop=True), exceptions_frame(records)
