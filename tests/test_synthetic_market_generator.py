from __future__ import annotations

from ev_flex_trading.ingestion.synthetic_market_generator import generate_synthetic_market_prices


def test_synthetic_market_generator_produces_complete_day() -> None:
    frame = generate_synthetic_market_prices(service_date="2026-05-09", random_seed=1)

    assert len(frame) == 48
    assert frame["settlement_period"].tolist() == list(range(1, 49))
    assert frame["price_gbp_per_mwh"].notna().all()


def test_synthetic_market_generator_is_deterministic() -> None:
    first = generate_synthetic_market_prices(service_date="2026-05-09", random_seed=7)
    second = generate_synthetic_market_prices(service_date="2026-05-09", random_seed=7)

    assert first["price_gbp_per_mwh"].tolist() == second["price_gbp_per_mwh"].tolist()


def test_negative_overnight_scenario_allows_negative_prices() -> None:
    frame = generate_synthetic_market_prices(
        service_date="2026-05-09",
        random_seed=3,
        scenario="negative_price_overnight",
    )

    assert (frame["price_gbp_per_mwh"] < 0).any()


def test_missing_interval_scenario_drops_periods() -> None:
    frame = generate_synthetic_market_prices(
        service_date="2026-05-09",
        scenario="missing_intervals_for_validation_demo",
    )

    assert len(frame) == 46
    assert 7 not in set(frame["settlement_period"])
    assert 8 not in set(frame["settlement_period"])
