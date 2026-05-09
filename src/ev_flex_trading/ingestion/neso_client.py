"""Lightweight optional NESO Data Portal CKAN client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen


class NesoClientError(RuntimeError):
    """Raised when the optional NESO client cannot complete a request."""


RequestJson = Callable[[str, dict[str, Any] | None, float], dict[str, Any]]


def _default_request_json(
    url: str, params: dict[str, Any] | None, timeout: float
) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    try:
        with urlopen(f"{url}{query}", timeout=timeout) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise NesoClientError(str(exc)) from exc

    if payload.get("success") is False:
        raise NesoClientError(str(payload.get("error", "NESO API returned success=false")))
    return payload


@dataclass
class NesoClient:
    base_url: str = "https://api.neso.energy/api/3/action"
    timeout: float = 20.0
    request_json: RequestJson = _default_request_json

    def _action(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request_json(f"{self.base_url}/{action}", params, self.timeout)

    def package_search(self, query: str) -> dict[str, Any]:
        return self._action("package_search", {"q": query})

    def resource_search(self, query: str) -> dict[str, Any]:
        return self._action("resource_search", {"query": query})

    def resource_show(self, resource_id: str) -> dict[str, Any]:
        return self._action("resource_show", {"id": resource_id})

    def datastore_search(
        self,
        resource_id: str,
        *,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"resource_id": resource_id, "limit": limit}
        if filters:
            params["filters"] = json.dumps(filters)
        return self._action("datastore_search", params)
