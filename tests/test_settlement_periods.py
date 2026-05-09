from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from ev_flex_trading.utils.settlement_periods import (
    generate_settlement_periods,
    timestamp_to_settlement_period,
    validate_half_hourly_coverage,
)


def test_generate_normal_day_has_48_periods() -> None:
    periods = generate_settlement_periods("2026-05-09")

    assert len(periods) == 48
    assert periods["settlement_period"].iloc[0] == 1
    assert periods["settlement_period"].iloc[-1] == 48


def test_generate_spring_dst_day_has_46_periods() -> None:
    periods = generate_settlement_periods("2026-03-29")

    assert len(periods) == 46


def test_generate_autumn_dst_day_has_50_periods() -> None:
    periods = generate_settlement_periods("2026-10-25")

    assert len(periods) == 50


def test_timestamp_to_settlement_period_mapping() -> None:
    timestamp = datetime(2026, 5, 9, 0, 30, tzinfo=ZoneInfo("Europe/London"))

    mapped = timestamp_to_settlement_period(timestamp)

    assert mapped.settlement_date.isoformat() == "2026-05-09"
    assert mapped.settlement_period == 2


def test_validate_half_hourly_coverage_detects_missing_and_duplicates() -> None:
    frame = pd.DataFrame({"settlement_period": [1, 2, 2, 4]})

    result = validate_half_hourly_coverage(frame, "2026-05-09")

    assert result["duplicate_periods"] == [2]
    assert 3 in result["missing_periods"]
    assert 48 in result["missing_periods"]
