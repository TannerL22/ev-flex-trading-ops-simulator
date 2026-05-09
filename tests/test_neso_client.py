from __future__ import annotations

from ev_flex_trading.ingestion.neso_client import NesoClient, NesoClientError


def test_neso_client_package_search_params() -> None:
    calls = []

    def fake_request(url, params, timeout):  # noqa: ANN001, ANN202
        calls.append((url, params, timeout))
        return {"success": True, "result": {"results": []}}

    client = NesoClient(
        base_url="https://example.test/api/3/action", timeout=6, request_json=fake_request
    )
    client.package_search("demand")

    assert calls[0][0] == "https://example.test/api/3/action/package_search"
    assert calls[0][1] == {"q": "demand"}
    assert calls[0][2] == 6


def test_neso_client_datastore_search_filters_are_json_encoded() -> None:
    calls = []

    def fake_request(url, params, timeout):  # noqa: ANN001, ANN202, ARG001
        calls.append((url, params))
        return {"success": True, "result": {"records": []}}

    client = NesoClient(base_url="https://example.test/api/3/action", request_json=fake_request)
    client.datastore_search("resource-1", limit=5, filters={"settlementDate": "2026-05-09"})

    assert calls[0][0].endswith("/datastore_search")
    assert calls[0][1]["resource_id"] == "resource-1"
    assert calls[0][1]["limit"] == 5
    assert "settlementDate" in calls[0][1]["filters"]


def test_neso_client_error_can_be_raised_by_injected_request() -> None:
    def fake_request(url, params, timeout):  # noqa: ANN001, ANN202, ARG001
        raise NesoClientError("api unavailable")

    client = NesoClient(base_url="https://example.test/api/3/action", request_json=fake_request)

    try:
        client.resource_show("resource-1")
    except NesoClientError as exc:
        assert "api unavailable" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected NesoClientError")
