"""Timezone helpers used by settlement-period calculations."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from ev_flex_trading.config import DEFAULT_TIMEZONE

GB_TZ = ZoneInfo(DEFAULT_TIMEZONE)


def as_gb_timestamp(value: datetime | str) -> datetime:
    """Return a timezone-aware Europe/London datetime.

    Naive inputs are interpreted as local GB clock time. Aware inputs are converted
    to Europe/London.
    """

    timestamp = datetime.fromisoformat(value) if isinstance(value, str) else value
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=GB_TZ)
    return timestamp.astimezone(GB_TZ)
