from __future__ import annotations

from ev_flex_trading.fleet.charging_windows import build_charging_window_intervals


def test_charging_window_same_day() -> None:
    intervals, exceptions = build_charging_window_intervals(
        arrival_time="2026-05-09T19:00:00+01:00",
        departure_time="2026-05-09T21:00:00+01:00",
        run_id="test",
        entity_id="EV-001",
    )

    assert len(intervals) == 4
    assert intervals["timestamp"].iloc[0].hour == 19
    assert exceptions.empty


def test_charging_window_overnight() -> None:
    intervals, exceptions = build_charging_window_intervals(
        arrival_time="2026-05-09T22:30:00+01:00",
        departure_time="2026-05-10T05:30:00+01:00",
        run_id="test",
        entity_id="EV-001",
    )

    assert len(intervals) == 14
    assert intervals["timestamp"].iloc[-1].hour == 5
    assert intervals["timestamp"].iloc[-1].minute == 0
    assert exceptions.empty


def test_charging_window_rounds_to_half_hours() -> None:
    intervals, exceptions = build_charging_window_intervals(
        arrival_time="2026-05-09T19:10:00+01:00",
        departure_time="2026-05-09T20:50:00+01:00",
        run_id="test",
        entity_id="EV-001",
    )

    assert len(intervals) == 2
    assert intervals["timestamp"].iloc[0].hour == 19
    assert intervals["timestamp"].iloc[0].minute == 30
    assert any(exceptions["message"].str.contains("rounded"))


def test_charging_window_no_valid_interval() -> None:
    intervals, exceptions = build_charging_window_intervals(
        arrival_time="2026-05-09T19:10:00+01:00",
        departure_time="2026-05-09T19:20:00+01:00",
        run_id="test",
        entity_id="EV-001",
    )

    assert intervals.empty
    assert any(exceptions["message"].str.contains("No valid half-hour"))


def test_charging_window_dst_autumn_edge_case() -> None:
    intervals, _ = build_charging_window_intervals(
        arrival_time="2026-10-25T00:00:00+01:00",
        departure_time="2026-10-25T03:00:00+00:00",
        run_id="test",
        entity_id="EV-001",
    )

    assert len(intervals) == 8
