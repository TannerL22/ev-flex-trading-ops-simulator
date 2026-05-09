"""Charging-window utilities for half-hourly EV charging schedules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from ev_flex_trading.config import DEFAULT_TIMEZONE
from ev_flex_trading.utils.settlement_periods import timestamp_to_settlement_period
from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception

INTERVAL_HOURS = 0.5


def ceil_to_half_hour(timestamp: datetime | str | pd.Timestamp) -> pd.Timestamp:
    """Round a timestamp up to the next half-hour boundary."""

    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize(DEFAULT_TIMEZONE)
    else:
        ts = ts.tz_convert(DEFAULT_TIMEZONE)
    return ts.ceil("30min")


def floor_to_half_hour(timestamp: datetime | str | pd.Timestamp) -> pd.Timestamp:
    """Round a timestamp down to the previous half-hour boundary."""

    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize(DEFAULT_TIMEZONE)
    else:
        ts = ts.tz_convert(DEFAULT_TIMEZONE)
    return ts.floor("30min")


def build_charging_window_intervals(
    *,
    arrival_time: datetime | str | pd.Timestamp,
    departure_time: datetime | str | pd.Timestamp,
    run_id: str,
    entity_id: Any,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return valid half-hour charging intervals and rounding exceptions.

    Phase 3 uses a simple interval-boundary assumption: arrival is rounded up
    to the next half-hour, and departure is rounded down to the previous
    half-hour. Intervals are included when their start is on or after rounded
    arrival and their end is on or before rounded departure.
    """

    records = []
    exceptions = []
    now = datetime.now(timezone.utc)
    arrival = pd.Timestamp(arrival_time)
    departure = pd.Timestamp(departure_time)
    if arrival.tzinfo is None:
        arrival = arrival.tz_localize(DEFAULT_TIMEZONE)
    else:
        arrival = arrival.tz_convert(DEFAULT_TIMEZONE)
    if departure.tzinfo is None:
        departure = departure.tz_localize(DEFAULT_TIMEZONE)
    else:
        departure = departure.tz_convert(DEFAULT_TIMEZONE)

    rounded_arrival = ceil_to_half_hour(arrival)
    rounded_departure = floor_to_half_hour(departure)

    if rounded_arrival != arrival or rounded_departure != departure:
        lost_minutes = (
            (rounded_arrival - arrival).total_seconds()
            + (departure - rounded_departure).total_seconds()
        ) / 60.0
        exceptions.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="low",
                category="fleet_data",
                entity_id=entity_id,
                message="Charging window rounded to half-hour boundaries.",
                suggested_action=(
                    f"Review if {lost_minutes:.0f} minutes of rounded time materially affects readiness."
                ),
            )
        )

    if rounded_departure <= rounded_arrival:
        exceptions.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="high",
                category="fleet_data",
                entity_id=entity_id,
                message="No valid half-hour charging intervals between arrival and departure.",
                suggested_action="Review arrival/departure times or allow partial-interval handling.",
            )
        )
        return pd.DataFrame(
            columns=[
                "timestamp",
                "interval_end",
                "settlement_date",
                "settlement_period",
                "interval_hours",
            ]
        ), exceptions_frame(exceptions)

    current = rounded_arrival
    while current + timedelta(minutes=30) <= rounded_departure:
        mapped = timestamp_to_settlement_period(current.to_pydatetime())
        records.append(
            {
                "timestamp": current,
                "interval_end": current + timedelta(minutes=30),
                "settlement_date": mapped.settlement_date,
                "settlement_period": mapped.settlement_period,
                "interval_hours": INTERVAL_HOURS,
            }
        )
        current += timedelta(minutes=30)

    return pd.DataFrame.from_records(records), exceptions_frame(exceptions)
