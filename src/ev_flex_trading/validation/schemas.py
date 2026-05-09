"""Reusable dataframe schema definitions.

The project keeps Phase 1 schema validation lightweight and dataframe-oriented.
`pyproject.toml` includes Pydantic for later row/config models, but these schemas
avoid introducing a heavier dataframe validation framework before the data model
stabilizes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

import pandas as pd
from pydantic import BaseModel, Field, field_validator


@dataclass(frozen=True)
class ColumnRule:
    name: str
    required: bool = True
    validator: Callable[[pd.Series], pd.Series] | None = None
    message: str = "invalid value"


@dataclass(frozen=True)
class DataFrameSchema:
    name: str
    columns: tuple[ColumnRule, ...]

    @property
    def required_columns(self) -> list[str]:
        return [column.name for column in self.columns if column.required]


class _NonEmptyModel(BaseModel):
    @field_validator("*", mode="after")
    @classmethod
    def _strip_empty_strings(cls, value):  # noqa: ANN001, ANN206
        if isinstance(value, str) and not value.strip():
            raise ValueError("must be non-empty")
        return value


class FleetScheduleRecord(_NonEmptyModel):
    service_date: date
    depot_id: str
    vehicle_id: str
    vehicle_type: str
    arrival_time: datetime
    departure_time: datetime
    battery_kwh: float = Field(gt=0)
    start_soc_pct: float = Field(ge=0, le=100)
    target_soc_pct: float = Field(ge=0, le=100)
    max_charger_kw: float = Field(gt=0)
    assigned_charger_id: str
    priority: str
    route_block: str

    @field_validator("target_soc_pct")
    @classmethod
    def target_soc_is_not_negative(cls, value: float) -> float:
        return value


class MarketPriceRecord(_NonEmptyModel):
    timestamp: datetime
    settlement_date: date
    settlement_period: int = Field(gt=0)
    price_gbp_per_mwh: float
    source: str
    market: str
    price_type: str = "unknown"
    currency: str = "GBP"
    unit: str = "MWh"


class ActualChargingRecord(_NonEmptyModel):
    timestamp: datetime
    depot_id: str
    vehicle_id: str
    meter_kwh: float = Field(ge=0)
    charger_id: str
    data_source: str


class ExceptionRecord(_NonEmptyModel):
    run_id: str
    timestamp: datetime
    severity: str
    category: str
    entity_id: str = ""
    message: str
    suggested_action: str

    @field_validator("severity")
    @classmethod
    def severity_allowed(cls, value: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if value not in allowed:
            raise ValueError(f"severity must be one of {sorted(allowed)}")
        return value


def _non_empty(series: pd.Series) -> pd.Series:
    return series.notna() & series.astype(str).str.strip().ne("")


def _positive(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce") > 0


def _non_negative(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce") >= 0


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").notna()


def _soc(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.between(0, 100, inclusive="both")


def _timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").notna()


FLEET_SCHEDULE_SCHEMA = DataFrameSchema(
    name="fleet_schedule",
    columns=(
        ColumnRule("service_date"),
        ColumnRule("depot_id", validator=_non_empty, message="depot_id must be non-empty"),
        ColumnRule("vehicle_id", validator=_non_empty, message="vehicle_id must be non-empty"),
        ColumnRule("vehicle_type", validator=_non_empty, message="vehicle_type must be non-empty"),
        ColumnRule("arrival_time", validator=_timestamp, message="arrival_time must be parseable"),
        ColumnRule(
            "departure_time", validator=_timestamp, message="departure_time must be parseable"
        ),
        ColumnRule("battery_kwh", validator=_positive, message="battery_kwh must be > 0"),
        ColumnRule(
            "start_soc_pct", validator=_soc, message="start_soc_pct must be between 0 and 100"
        ),
        ColumnRule(
            "target_soc_pct", validator=_soc, message="target_soc_pct must be between 0 and 100"
        ),
        ColumnRule("max_charger_kw", validator=_positive, message="max_charger_kw must be > 0"),
        ColumnRule(
            "assigned_charger_id",
            validator=_non_empty,
            message="assigned_charger_id must be non-empty",
        ),
        ColumnRule("priority", validator=_non_empty, message="priority must be non-empty"),
        ColumnRule("route_block", validator=_non_empty, message="route_block must be non-empty"),
    ),
)

MARKET_PRICE_SCHEMA = DataFrameSchema(
    name="market_price",
    columns=(
        ColumnRule("timestamp", validator=_timestamp, message="timestamp must be parseable"),
        ColumnRule("settlement_date"),
        ColumnRule("settlement_period"),
        ColumnRule(
            "price_gbp_per_mwh",
            validator=_numeric,
            message="price_gbp_per_mwh must be numeric",
        ),
        ColumnRule("source", validator=_non_empty, message="source must be non-empty"),
        ColumnRule("market", validator=_non_empty, message="market must be non-empty"),
        ColumnRule("price_type", required=False),
        ColumnRule("currency", required=False),
        ColumnRule("unit", required=False),
        ColumnRule("ingestion_timestamp", required=False),
        ColumnRule("data_quality_flag", required=False),
        ColumnRule("notes", required=False),
    ),
)

ACTUAL_CHARGING_SCHEMA = DataFrameSchema(
    name="actual_charging",
    columns=(
        ColumnRule("timestamp", validator=_timestamp, message="timestamp must be parseable"),
        ColumnRule("depot_id", validator=_non_empty, message="depot_id must be non-empty"),
        ColumnRule("vehicle_id", validator=_non_empty, message="vehicle_id must be non-empty"),
        ColumnRule("meter_kwh", validator=_non_negative, message="meter_kwh must be >= 0"),
        ColumnRule("charger_id", validator=_non_empty, message="charger_id must be non-empty"),
        ColumnRule("data_source", validator=_non_empty, message="data_source must be non-empty"),
    ),
)

EXCEPTIONS_SCHEMA = DataFrameSchema(
    name="exceptions",
    columns=(
        ColumnRule("run_id", validator=_non_empty, message="run_id must be non-empty"),
        ColumnRule("timestamp", validator=_timestamp, message="timestamp must be parseable"),
        ColumnRule("severity", validator=_non_empty, message="severity must be non-empty"),
        ColumnRule("category", validator=_non_empty, message="category must be non-empty"),
        ColumnRule("entity_id"),
        ColumnRule("message", validator=_non_empty, message="message must be non-empty"),
        ColumnRule(
            "suggested_action", validator=_non_empty, message="suggested_action must be non-empty"
        ),
    ),
)
