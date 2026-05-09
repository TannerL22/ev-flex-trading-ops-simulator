"""Loader for synthetic/sample EPEX-style CSV files.

These files are public-demo inputs only. They are not official EPEX data and do
not require access to a paid market feed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ev_flex_trading.ingestion.market_data_normalizer import normalize_market_prices


def load_epex_style_csv(
    path: str | Path,
    *,
    service_date: str | None = None,
    default_market: str = "day_ahead",
    default_source: str = "sample_epex_csv",
    run_id: str = "epex_csv_loader",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and normalize a local EPEX-style sample CSV.

    Supported sample columns:
    - `delivery_date`
    - `settlement_period`
    - `delivery_start`
    - `delivery_end`
    - `price_gbp_per_mwh`
    - `market`
    - `source`
    - optional `price_type`, `currency`, `unit`, `notes`
    """

    raw = pd.read_csv(path)
    return normalize_market_prices(
        raw,
        service_date=service_date,
        default_source=default_source,
        default_market=default_market,
        default_price_type="auction_clearing",
        run_id=run_id,
    )
