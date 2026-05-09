from __future__ import annotations

from ev_flex_trading.ingestion.elexon_client import (
    ElexonClient,
    ElexonClientError,
    normalize_elexon_system_prices,
)


def test_elexon_client_builds_date_url() -> None:
    calls = []

    def fake_request(url, params, timeout):  # noqa: ANN001, ANN202
        calls.append((url, params, timeout))
        return {"data": []}

    client = ElexonClient(base_url="https://example.test", timeout=5, request_json=fake_request)
    client.fetch_system_prices_for_date("2026-05-09")

    assert calls[0][0] == "https://example.test/balancing/settlement/system-prices/2026-05-09"
    assert calls[0][1] == {"format": "json"}
    assert calls[0][2] == 5


def test_normalize_elexon_system_prices_from_mock_payload() -> None:
    payload = {
        "data": [
            {"settlementDate": "2026-05-09", "settlementPeriod": 1, "systemBuyPrice": 95.25},
            {"settlementDate": "2026-05-09", "settlementPeriod": 2, "systemSellPrice": 88.0},
        ]
    }

    normalized, exceptions = normalize_elexon_system_prices(
        payload,
        settlement_date="2026-05-09",
        run_id="test",
    )

    assert normalized.loc[0, "source"] == "elexon_insights"
    assert normalized.loc[0, "market"] == "system_price"
    assert normalized.loc[0, "price_gbp_per_mwh"] == 95.25
    assert not exceptions.empty


def test_elexon_client_error_can_be_raised_by_injected_request() -> None:
    def fake_request(url, params, timeout):  # noqa: ANN001, ANN202, ARG001
        raise ElexonClientError("network unavailable")

    client = ElexonClient(base_url="https://example.test", request_json=fake_request)

    try:
        client.fetch_system_prices_for_date("2026-05-09")
    except ElexonClientError as exc:
        assert "network unavailable" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ElexonClientError")
