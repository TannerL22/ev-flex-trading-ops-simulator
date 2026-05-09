from __future__ import annotations

import pandas as pd

from ev_flex_trading.ingestion.epex_csv_loader import load_epex_style_csv
from ev_flex_trading.ingestion.synthetic_market_generator import generate_synthetic_market_prices


def test_load_epex_style_csv_normalizes_full_day(tmp_path) -> None:  # noqa: ANN001
    synthetic = generate_synthetic_market_prices(
        service_date="2026-05-09",
        random_seed=9,
        market="day_ahead",
        source="sample_epex_csv",
    )
    raw = pd.DataFrame(
        {
            "delivery_date": synthetic["settlement_date"],
            "settlement_period": synthetic["settlement_period"],
            "delivery_start": synthetic["timestamp"],
            "delivery_end": pd.to_datetime(synthetic["timestamp"]) + pd.Timedelta(minutes=30),
            "price_gbp_per_mwh": synthetic["price_gbp_per_mwh"],
            "market": "day_ahead",
            "source": "sample_epex_csv",
        }
    )
    path = tmp_path / "epex_day_ahead_sample.csv"
    raw.to_csv(path, index=False)

    normalized, exceptions = load_epex_style_csv(path, service_date="2026-05-09")

    assert len(normalized) == 48
    assert normalized["settlement_period"].tolist() == list(range(1, 49))
    assert exceptions.empty


def test_load_epex_style_csv_reports_bad_price(tmp_path) -> None:  # noqa: ANN001
    raw = pd.DataFrame(
        {
            "delivery_date": ["2026-05-09"],
            "settlement_period": [1],
            "price_gbp_per_mwh": ["bad"],
            "market": ["day_ahead"],
            "source": ["sample_epex_csv"],
        }
    )
    path = tmp_path / "bad.csv"
    raw.to_csv(path, index=False)

    _, exceptions = load_epex_style_csv(path, service_date="2026-05-09")

    assert any(exceptions["message"].str.contains("price_gbp_per_mwh must be numeric"))
