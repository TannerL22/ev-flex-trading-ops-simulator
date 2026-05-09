from __future__ import annotations

import pandas as pd

from ev_flex_trading.ingestion.market_data_normalizer import normalize_market_prices
from ev_flex_trading.ingestion.synthetic_market_generator import generate_synthetic_market_prices
from ev_flex_trading.validation.data_quality_checks import check_market_price_quality


def test_normalize_market_prices_from_timestamp_format() -> None:
    raw = pd.DataFrame(
        {
            "timestamp": ["2026-05-09T00:00:00+01:00", "2026-05-09T00:30:00+01:00"],
            "price_gbp_per_mwh": [50.0, -5.0],
            "market": ["day_ahead", "day_ahead"],
            "source": ["test", "test"],
        }
    )

    normalized, exceptions = normalize_market_prices(
        raw,
        service_date="2026-05-09",
        default_price_type="auction_clearing",
        run_id="test",
    )

    assert normalized.loc[0, "settlement_period"] == 1
    assert normalized.loc[1, "settlement_period"] == 2
    assert normalized.loc[1, "price_gbp_per_mwh"] == -5.0
    assert not exceptions.empty
    assert any(exceptions["message"].str.contains("Missing half-hourly market interval"))


def test_normalize_market_prices_from_delivery_period_format() -> None:
    raw = pd.DataFrame(
        {
            "delivery_date": ["2026-05-09"],
            "settlement_period": [3],
            "price_gbp_per_mwh": [55.5],
            "market": ["day_ahead"],
            "source": ["sample_epex_csv"],
        }
    )

    normalized, _ = normalize_market_prices(raw, service_date="2026-05-09", run_id="test")

    assert normalized.loc[0, "settlement_period"] == 3
    assert normalized.loc[0, "timestamp"].hour == 1


def test_market_quality_detects_implausible_price_and_mixed_units() -> None:
    frame = generate_synthetic_market_prices(service_date="2026-05-09")
    frame.loc[0, "price_gbp_per_mwh"] = 1500
    frame.loc[1, "unit"] = "kWh"

    exceptions = check_market_price_quality(frame, service_date="2026-05-09", run_id="test")

    assert any(exceptions["message"].str.contains("Implausible market price"))
    assert any(exceptions["message"].str.contains("Mixed price units"))


def test_market_quality_detects_missing_intervals() -> None:
    frame = generate_synthetic_market_prices(
        service_date="2026-05-09",
        scenario="missing_intervals_for_validation_demo",
    )

    exceptions = check_market_price_quality(frame, service_date="2026-05-09", run_id="test")

    assert any(exceptions["message"].str.contains("Missing half-hourly market interval"))
