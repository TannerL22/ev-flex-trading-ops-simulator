"""Structured exception records for analyst review."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

EXCEPTION_COLUMNS = [
    "run_id",
    "timestamp",
    "severity",
    "category",
    "entity_id",
    "message",
    "suggested_action",
]

VALID_SEVERITIES = {"low", "medium", "high", "critical"}


def make_exception(
    *,
    run_id: str,
    severity: str,
    category: str,
    entity_id: Any,
    message: str,
    suggested_action: str,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")
    return {
        "run_id": run_id,
        "timestamp": timestamp or datetime.now(timezone.utc),
        "severity": severity,
        "category": category,
        "entity_id": "" if entity_id is None else str(entity_id),
        "message": message,
        "suggested_action": suggested_action,
    }


def exceptions_frame(records: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    return pd.DataFrame.from_records(records or [], columns=EXCEPTION_COLUMNS)
