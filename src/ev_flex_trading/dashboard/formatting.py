"""Formatting helpers for dashboard metrics and labels."""

from __future__ import annotations

import pandas as pd


def safe_float(value: object, default: float = 0.0) -> float:
    """Convert a value to float, returning a default for missing or invalid values."""

    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return default
    return float(number)


def safe_int(value: object, default: int = 0) -> int:
    """Convert a value to int, returning a default for missing or invalid values."""

    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return default
    return int(round(float(number)))


def format_integer(value: object) -> str:
    """Format a count."""

    return f"{safe_int(value):,}"


def format_gbp(value: object, *, decimals: int = 2) -> str:
    """Format a GBP value."""

    return f"£{safe_float(value):,.{decimals}f}"


def format_gbp_per_mwh(value: object) -> str:
    """Format a GBP/MWh value."""

    return f"£{safe_float(value):,.2f}/MWh"


def format_mwh(value: object) -> str:
    """Format a MWh value."""

    return f"{safe_float(value):,.3f} MWh"


def format_kwh(value: object) -> str:
    """Format a kWh value."""

    return f"{safe_float(value):,.1f} kWh"


def format_kw(value: object) -> str:
    """Format a kW value."""

    return f"{safe_float(value):,.1f} kW"


def format_pct(value: object) -> str:
    """Format percentage values stored as either percent points or fractions."""

    number = safe_float(value)
    if abs(number) <= 1:
        number *= 100
    return f"{number:,.1f}%"
