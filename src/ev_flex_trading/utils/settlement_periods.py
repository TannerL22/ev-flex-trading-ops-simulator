"""GB half-hourly settlement-period utilities.

Settlement periods are generated from local GB midnight to the next local
midnight using UTC as the continuous timeline. This produces 48 periods on
normal days, 46 on spring clock-change days, and 50 on autumn clock-change days.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from ev_flex_trading.config import DEFAULT_TIMEZONE

GB_TZ = ZoneInfo(DEFAULT_TIMEZONE)
HALF_HOUR = timedelta(minutes=30)


@dataclass(frozen=True)
class SettlementPeriod:
    settlement_date: date
    settlement_period: int
    period_start: datetime
    period_end: datetime


def _local_midnight(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=GB_TZ)


def generate_settlement_periods(service_date: date | str) -> pd.DataFrame:
    """Generate all GB settlement periods for a local service date."""

    local_date = date.fromisoformat(service_date) if isinstance(service_date, str) else service_date
    start_utc = _local_midnight(local_date).astimezone(timezone.utc)
    end_utc = _local_midnight(local_date + timedelta(days=1)).astimezone(timezone.utc)

    starts_utc: list[datetime] = []
    current = start_utc
    while current < end_utc:
        starts_utc.append(current)
        current += HALF_HOUR

    records = []
    for index, start in enumerate(starts_utc, start=1):
        period_start = start.astimezone(GB_TZ)
        period_end = (start + HALF_HOUR).astimezone(GB_TZ)
        records.append(
            {
                "settlement_date": local_date,
                "settlement_period": index,
                "period_start": period_start,
                "period_end": period_end,
            }
        )
    return pd.DataFrame.from_records(records)


def timestamp_to_settlement_period(timestamp: datetime | str) -> SettlementPeriod:
    """Map a timestamp to the GB settlement period containing it."""

    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize(DEFAULT_TIMEZONE)
    else:
        ts = ts.tz_convert(DEFAULT_TIMEZONE)

    periods = generate_settlement_periods(ts.date())
    for row in periods.itertuples(index=False):
        if row.period_start <= ts.to_pydatetime() < row.period_end:
            return SettlementPeriod(
                settlement_date=row.settlement_date,
                settlement_period=int(row.settlement_period),
                period_start=row.period_start,
                period_end=row.period_end,
            )

    raise ValueError(f"Timestamp {timestamp!r} is outside generated settlement periods")


def add_settlement_columns(
    frame: pd.DataFrame,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """Return a copy with `settlement_date` and `settlement_period` columns."""

    result = frame.copy()
    mapped = result[timestamp_col].apply(timestamp_to_settlement_period)
    result["settlement_date"] = mapped.apply(lambda item: item.settlement_date)
    result["settlement_period"] = mapped.apply(lambda item: item.settlement_period)
    return result


def validate_half_hourly_coverage(
    frame: pd.DataFrame,
    service_date: date | str,
    settlement_period_col: str = "settlement_period",
) -> dict[str, list[int]]:
    """Return missing and duplicate settlement periods for a local date."""

    expected = set(generate_settlement_periods(service_date)["settlement_period"].astype(int))
    observed_series = frame[settlement_period_col].dropna().astype(int)
    observed = set(observed_series)
    duplicates = sorted(
        int(period) for period, count in observed_series.value_counts().items() if count > 1
    )
    return {
        "missing_periods": sorted(expected - observed),
        "duplicate_periods": duplicates,
    }
