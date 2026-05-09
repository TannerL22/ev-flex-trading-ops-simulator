"""Market participation metrics for daily trading support summaries."""

from __future__ import annotations

import pandas as pd


def calculate_market_participation_metrics(
    reconciliation: pd.DataFrame,
    market_prices: pd.DataFrame,
    *,
    run_id: str,
    scenario: str,
) -> pd.DataFrame:
    """Return one-row operational market participation metrics."""

    scheduled = reconciliation["scheduled_mwh"].fillna(0.0)
    actual = reconciliation["actual_mwh"].fillna(0.0)
    deviation = reconciliation["deviation_mwh"].fillna(0.0)
    active = scheduled > 0
    prices = market_prices.copy()
    prices["settlement_date"] = prices["settlement_date"].astype(str)
    rec = reconciliation.copy()
    rec["settlement_date"] = rec["settlement_date"].astype(str)
    priced = rec.merge(
        prices[["settlement_date", "settlement_period", "price_gbp_per_mwh"]],
        on=["settlement_date", "settlement_period"],
        how="left",
    )

    return pd.DataFrame.from_records(
        [
            {
                "run_id": run_id,
                "scenario": scenario,
                "total_scheduled_mwh": float(scheduled.sum()),
                "total_actual_mwh": float(actual.sum()),
                "active_settlement_periods": int(active.sum()),
                "average_scheduled_mw": (
                    float(reconciliation.loc[active, "scheduled_kw"].mean() / 1000.0)
                    if active.any()
                    else 0.0
                ),
                "peak_scheduled_mw": float(reconciliation["scheduled_kw"].max() / 1000.0),
                "peak_actual_mw": float(reconciliation["actual_kw"].max(skipna=True) / 1000.0),
                "mean_absolute_deviation_mwh": float(deviation.abs().mean()),
                "mean_absolute_percentage_deviation": float(
                    reconciliation["deviation_pct"].abs().mean(skipna=True)
                ),
                "material_deviation_interval_count": int(
                    reconciliation["reconciliation_status"].eq("material_deviation").sum()
                ),
                "missing_actual_interval_count": int(
                    reconciliation["reconciliation_status"].eq("missing_actual").sum()
                ),
                "intervals_with_negative_prices": int((priced["price_gbp_per_mwh"] < 0).sum()),
                "intervals_with_positive_deviation": int((deviation > 0).sum()),
                "intervals_with_negative_deviation": int((deviation < 0).sum()),
            }
        ]
    )
