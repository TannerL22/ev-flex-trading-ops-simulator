"""Simplified settlement-style exposure simulation."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ev_flex_trading.validation.exceptions import exceptions_frame, make_exception


def simulate_settlement_style_exposure(
    reconciliation: pd.DataFrame,
    market_prices: pd.DataFrame,
    *,
    run_id: str = "phase5_settlement_style",
    positive_deviation_spread_gbp_per_mwh: float = 25.0,
    negative_deviation_spread_gbp_per_mwh: float = -15.0,
    pricing_method: str = "synthetic_imbalance_spread",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate simplified settlement-style exposure from deviations."""

    exceptions = []
    now = datetime.now(timezone.utc)
    prices = market_prices.copy()
    prices["settlement_date"] = prices["settlement_date"].astype(str)
    prices = prices.drop_duplicates(["settlement_date", "settlement_period"], keep="first")
    frame = reconciliation.copy()
    frame["settlement_date"] = frame["settlement_date"].astype(str)
    merged = frame.merge(
        prices[["settlement_date", "settlement_period", "price_gbp_per_mwh"]],
        on=["settlement_date", "settlement_period"],
        how="left",
    )
    merged = merged.rename(columns={"price_gbp_per_mwh": "scheduled_price_gbp_per_mwh"})

    missing_price = merged["scheduled_price_gbp_per_mwh"].isna()
    for row in merged[missing_price].itertuples():
        exceptions.append(
            make_exception(
                run_id=run_id,
                timestamp=now,
                severity="critical",
                category="settlement",
                entity_id=f"SP{row.settlement_period}",
                message="Missing market price for settlement-style simulation.",
                suggested_action="Provide complete price data before calculating exposure.",
            )
        )

    merged["imbalance_price_gbp_per_mwh"] = merged["scheduled_price_gbp_per_mwh"]
    positive = merged["deviation_mwh"] > 0
    negative = merged["deviation_mwh"] < 0
    merged.loc[positive, "imbalance_price_gbp_per_mwh"] = (
        merged.loc[positive, "scheduled_price_gbp_per_mwh"] + positive_deviation_spread_gbp_per_mwh
    )
    merged.loc[negative, "imbalance_price_gbp_per_mwh"] = (
        merged.loc[negative, "scheduled_price_gbp_per_mwh"] + negative_deviation_spread_gbp_per_mwh
    )
    deviation_for_exposure = merged["deviation_mwh"].fillna(0.0)
    merged["scheduled_cost_gbp"] = merged["scheduled_mwh"] * merged["scheduled_price_gbp_per_mwh"]
    merged["actual_energy_cost_gbp"] = merged["actual_mwh"] * merged["scheduled_price_gbp_per_mwh"]
    merged["imbalance_exposure_gbp"] = deviation_for_exposure * (
        merged["imbalance_price_gbp_per_mwh"] - merged["scheduled_price_gbp_per_mwh"]
    )
    merged["total_settlement_style_cost_gbp"] = (
        merged["scheduled_cost_gbp"] + merged["imbalance_exposure_gbp"]
    )
    merged["pricing_method"] = pricing_method
    merged["notes"] = "Simplified settlement-style exposure; not official settlement."
    merged["run_id"] = run_id

    return (
        merged[
            [
                "run_id",
                "service_date",
                "depot_id",
                "timestamp",
                "settlement_date",
                "settlement_period",
                "scheduled_mwh",
                "actual_mwh",
                "deviation_mwh",
                "scheduled_price_gbp_per_mwh",
                "imbalance_price_gbp_per_mwh",
                "scheduled_cost_gbp",
                "actual_energy_cost_gbp",
                "imbalance_exposure_gbp",
                "total_settlement_style_cost_gbp",
                "pricing_method",
                "notes",
            ]
        ],
        exceptions_frame(exceptions),
    )
