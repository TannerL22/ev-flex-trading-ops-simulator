"""Generate Phase 3 dumb-charging baseline outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ev_flex_trading.config import (
    OUTPUTS_DIR,
    PROCESSED_DIR,
    SAMPLE_INPUTS_DIR,
    ensure_data_directories,
)
from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.fleet.synthetic_fleet_generator import write_sample_fleet_schedule
from ev_flex_trading.ingestion.synthetic_market_generator import generate_synthetic_market_prices
from ev_flex_trading.optimisation.dumb_charging_baseline import (
    aggregate_depot_load,
    build_dumb_charging_baseline,
)
from ev_flex_trading.trading.baseline_costing import calculate_baseline_charging_cost
from ev_flex_trading.validation.data_quality_checks import check_fleet_schedule_quality

SERVICE_DATE = "2026-05-09"
RUN_ID = "phase3_baseline_sample"


def _load_or_generate_fleet() -> pd.DataFrame:
    path = SAMPLE_INPUTS_DIR / "ev_fleet_schedule_sample.csv"
    if not path.exists():
        return write_sample_fleet_schedule(service_date=SERVICE_DATE)
    return pd.read_csv(path)


def _load_or_generate_market_prices() -> pd.DataFrame:
    path = PROCESSED_DIR / "market_prices_synthetic_base.csv"
    if path.exists():
        return pd.read_csv(path)
    frame = generate_synthetic_market_prices(
        service_date=SERVICE_DATE,
        random_seed=100,
        scenario="base",
        market="synthetic_day_ahead",
    )
    frame.to_csv(path, index=False)
    return frame


def _ensure_market_prices_cover_depot_load(
    market_prices: pd.DataFrame,
    depot_load: pd.DataFrame,
) -> pd.DataFrame:
    if depot_load.empty:
        return market_prices

    prices = market_prices.copy()
    existing_dates = set(prices["settlement_date"].astype(str))
    required_dates = set(depot_load["settlement_date"].astype(str))
    missing_dates = sorted(required_dates - existing_dates)
    generated = [
        generate_synthetic_market_prices(
            service_date=missing_date,
            random_seed=200 + index,
            scenario="base",
            market="synthetic_day_ahead",
        )
        for index, missing_date in enumerate(missing_dates)
    ]
    if generated:
        prices = pd.concat([prices, *generated], ignore_index=True)
    return prices


def main() -> int:
    ensure_data_directories()
    fleet = _load_or_generate_fleet()
    market_prices = _load_or_generate_market_prices()

    fleet_exceptions = check_fleet_schedule_quality(fleet, run_id=RUN_ID)
    requirements = calculate_fleet_requirements(fleet)
    vehicle_schedule, schedule_exceptions = build_dumb_charging_baseline(
        requirements,
        run_id=RUN_ID,
    )
    depot_load = aggregate_depot_load(vehicle_schedule, run_id=RUN_ID)
    market_prices = _ensure_market_prices_cover_depot_load(market_prices, depot_load)
    cost_by_interval, summary, cost_exceptions = calculate_baseline_charging_cost(
        depot_load,
        market_prices,
        vehicle_schedule=vehicle_schedule,
        market="synthetic_day_ahead",
        source="synthetic",
        price_type="synthetic",
        run_id=RUN_ID,
    )

    exceptions = pd.concat(
        [fleet_exceptions, schedule_exceptions, cost_exceptions],
        ignore_index=True,
    )
    summary.loc[0, "exception_count"] = len(exceptions)

    outputs = {
        PROCESSED_DIR / "baseline_vehicle_schedule_sample.csv": vehicle_schedule,
        PROCESSED_DIR / "baseline_depot_load_sample.csv": depot_load,
        PROCESSED_DIR / "baseline_cost_by_interval_sample.csv": cost_by_interval,
        OUTPUTS_DIR / "phase3_baseline_summary_sample.csv": summary,
        OUTPUTS_DIR / "phase3_baseline_exceptions_sample.csv": exceptions,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)

    print("Phase 3 dumb-charging baseline generated")
    print(f"Service date: {SERVICE_DATE}")
    print(f"Vehicles: {requirements['vehicle_id'].nunique()}")
    print(f"Vehicle schedule rows: {len(vehicle_schedule)}")
    print(f"Depot load intervals: {len(depot_load)}")
    print(f"Total delivered MWh: {summary.loc[0, 'total_delivered_mwh']:.3f}")
    print(f"Baseline cost GBP: {summary.loc[0, 'total_baseline_cost_gbp']:.2f}")
    print(f"Exceptions: {len(exceptions)}")
    for path in outputs:
        print(f"Wrote {path.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
