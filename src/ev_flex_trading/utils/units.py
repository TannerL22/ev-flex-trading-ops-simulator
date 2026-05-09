"""Unit conversion helpers."""

from __future__ import annotations


def kwh_to_mwh(value_kwh: float) -> float:
    return value_kwh / 1000.0


def mwh_to_kwh(value_mwh: float) -> float:
    return value_mwh * 1000.0
