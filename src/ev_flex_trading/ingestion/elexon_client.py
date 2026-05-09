"""Lightweight optional ELEXON Insights API client.

ELEXON publishes GB balancing and settlement data through the Insights platform.
System Buy Price and System Sell Price are imbalance/cash-out prices by
settlement period. This client is intentionally small, mockable, and optional:
tests do not call the live API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from ev_flex_trading.ingestion.market_data_normalizer import normalize_market_prices
from ev_flex_trading.utils.settlement_periods import generate_settlement_periods
from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception


class ElexonClientError(RuntimeError):
    """Raised when the optional ELEXON client cannot complete a request."""


RequestJson = Callable[[str, dict[str, Any] | None, float], dict[str, Any]]


def _default_request_json(
    url: str, params: dict[str, Any] | None, timeout: float
) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    try:
        with urlopen(f"{url}{query}", timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise ElexonClientError(str(exc)) from exc


@dataclass
class ElexonClient:
    base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    timeout: float = 20.0
    request_json: RequestJson = _default_request_json

    def fetch_system_prices_for_date(self, settlement_date: date | str) -> dict[str, Any]:
        """Fetch system prices for a settlement date.

        Endpoint path follows the public Insights client convention used by
        generated clients: `/balancing/settlement/system-prices/{date}`.
        Live API field names can evolve, so normalization is defensive.
        """

        local_date = (
            date.fromisoformat(settlement_date)
            if isinstance(settlement_date, str)
            else settlement_date
        )
        url = f"{self.base_url}/balancing/settlement/system-prices/{local_date.isoformat()}"
        return self.request_json(url, {"format": "json"}, self.timeout)

    def fetch_system_price_for_period(
        self,
        settlement_date: date | str,
        settlement_period: int,
    ) -> dict[str, Any]:
        """Fetch one settlement-period price if supported by the live API."""

        local_date = (
            date.fromisoformat(settlement_date)
            if isinstance(settlement_date, str)
            else settlement_date
        )
        url = (
            f"{self.base_url}/balancing/settlement/system-prices/"
            f"{local_date.isoformat()}/{settlement_period}"
        )
        return self.request_json(url, {"format": "json"}, self.timeout)


def _records_from_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    data = payload.get("data", payload.get("results", payload.get("result", payload)))
    if isinstance(data, dict) and "records" in data:
        data = data["records"]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def normalize_elexon_system_prices(
    raw_payload: dict[str, Any] | list[dict[str, Any]],
    *,
    settlement_date: date | str,
    run_id: str = "elexon_system_prices",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize mocked or live-like ELEXON system price records."""

    local_date = (
        date.fromisoformat(settlement_date) if isinstance(settlement_date, str) else settlement_date
    )
    periods = generate_settlement_periods(local_date).set_index("settlement_period")
    rows = []
    records = []
    now = datetime.now(timezone.utc)

    for index, record in enumerate(_records_from_payload(raw_payload)):
        try:
            period = int(record.get("settlementPeriod", record.get("settlement_period")))
            price = record.get(
                "systemBuyPrice",
                record.get("systemSellPrice", record.get("price", record.get("systemPrice"))),
            )
            rows.append(
                {
                    "timestamp": periods.loc[period, "period_start"],
                    "settlement_date": local_date.isoformat(),
                    "settlement_period": period,
                    "price_gbp_per_mwh": price,
                    "source": "elexon_insights",
                    "market": "system_price",
                    "price_type": "system_buy",
                    "currency": "GBP",
                    "unit": "MWh",
                    "notes": "ELEXON system price normalization from API-like payload.",
                }
            )
        except Exception as exc:
            records.append(
                make_exception(
                    run_id=run_id,
                    timestamp=now,
                    severity="high",
                    category="market_data",
                    entity_id=index,
                    message=f"Could not normalize ELEXON system price record: {exc}",
                    suggested_action="Review live API field mapping or source record contents.",
                )
            )

    normalized, quality = normalize_market_prices(
        pd.DataFrame(rows),
        service_date=local_date,
        default_source="elexon_insights",
        default_market="system_price",
        default_price_type="system_buy",
        run_id=run_id,
    )
    records.extend(quality.to_dict("records"))
    return normalized, exceptions_frame(records)
