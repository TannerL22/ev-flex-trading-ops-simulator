"""Offline synthetic half-hourly market price generation."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from ev_flex_trading.utils.settlement_periods import generate_settlement_periods


def generate_synthetic_market_prices(
    *,
    service_date: date | str,
    random_seed: int = 42,
    base_price: float = 82.0,
    volatility: float = 9.0,
    evening_peak_multiplier: float = 1.45,
    overnight_discount: float = 0.62,
    allow_negative_prices: bool = False,
    market: str = "synthetic_day_ahead",
    source: str = "synthetic",
    scenario: str = "base",
) -> pd.DataFrame:
    """Generate a plausible daily GB half-hourly price curve.

    The shape is intentionally simple and transparent: lower overnight prices,
    morning/evening peaks, random noise, and optional negative or spike periods.
    """

    local_date = date.fromisoformat(service_date) if isinstance(service_date, str) else service_date
    rng = np.random.default_rng(random_seed)
    periods = generate_settlement_periods(local_date)
    hours = periods["period_start"].apply(lambda ts: ts.hour + ts.minute / 60.0).to_numpy()

    shape = np.ones(len(periods))
    shape[(hours < 5.5)] *= overnight_discount
    shape[(hours >= 7.0) & (hours <= 9.0)] *= 1.2
    shape[(hours >= 16.5) & (hours <= 19.5)] *= evening_peak_multiplier

    scenario_volatility = volatility
    if scenario == "high_volatility":
        scenario_volatility *= 2.3
    if scenario == "evening_spike":
        shape[(hours >= 17.0) & (hours <= 19.0)] *= 2.4
    if scenario == "negative_price_overnight":
        allow_negative_prices = True
        shape[(hours < 4.0)] *= 0.05

    prices = base_price * shape + rng.normal(0, scenario_volatility, len(periods))
    if allow_negative_prices:
        negative_mask = hours < 4.0
        prices[negative_mask] -= base_price * 0.55
    else:
        prices = np.maximum(prices, 0.0)

    frame = pd.DataFrame(
        {
            "timestamp": periods["period_start"],
            "settlement_date": periods["settlement_date"],
            "settlement_period": periods["settlement_period"],
            "price_gbp_per_mwh": np.round(prices, 2),
            "source": source,
            "market": market,
            "price_type": "synthetic",
            "currency": "GBP",
            "unit": "MWh",
            "ingestion_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
            "data_quality_flag": "ok",
            "notes": f"synthetic scenario: {scenario}",
        }
    )

    if scenario == "missing_intervals_for_validation_demo":
        frame = frame[~frame["settlement_period"].isin([7, 8])].reset_index(drop=True)

    return frame
