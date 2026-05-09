"""Generate Phase 4 smart-charging optimization outputs."""

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
from ev_flex_trading.optimisation.smart_charging_optimizer import optimize_smart_charging
from ev_flex_trading.trading.baseline_costing import calculate_baseline_charging_cost
from ev_flex_trading.trading.optimization_comparison import build_optimization_summary
from ev_flex_trading.validation.data_quality_checks import check_fleet_schedule_quality

SERVICE_DATE = "2026-05-09"
RUN_ID = "phase4_optimization_sample"


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


def _ensure_market_prices_cover_dates(
    market_prices: pd.DataFrame,
    settlement_dates: set[str],
) -> pd.DataFrame:
    prices = market_prices.copy()
    existing_dates = set(prices["settlement_date"].astype(str))
    missing_dates = sorted(settlement_dates - existing_dates)
    generated = [
        generate_synthetic_market_prices(
            service_date=missing_date,
            random_seed=300 + index,
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
    requirements = calculate_fleet_requirements(fleet)
    market_prices = _load_or_generate_market_prices()

    baseline_schedule, baseline_schedule_exceptions = build_dumb_charging_baseline(
        requirements,
        run_id=RUN_ID,
    )
    baseline_depot = aggregate_depot_load(baseline_schedule, run_id=RUN_ID)
    required_price_dates = set(baseline_depot["settlement_date"].astype(str))
    market_prices = _ensure_market_prices_cover_dates(market_prices, required_price_dates)
    baseline_cost, _, baseline_cost_exceptions = calculate_baseline_charging_cost(
        baseline_depot,
        market_prices,
        vehicle_schedule=baseline_schedule,
        market="synthetic_day_ahead",
        source="synthetic",
        price_type="synthetic",
        run_id=RUN_ID,
    )

    optimized_schedule, optimized_depot, optimized_cost, optimization_exceptions = (
        optimize_smart_charging(
            requirements,
            market_prices,
            run_id=RUN_ID,
            service_date=SERVICE_DATE,
            market="synthetic_day_ahead",
            source="synthetic",
            price_type="synthetic",
        )
    )
    exceptions = pd.concat(
        [
            check_fleet_schedule_quality(fleet, run_id=RUN_ID),
            baseline_schedule_exceptions,
            baseline_cost_exceptions,
            optimization_exceptions,
        ],
        ignore_index=True,
    )
    summary = build_optimization_summary(
        optimized_vehicle_schedule=optimized_schedule,
        optimized_depot_load=optimized_depot,
        optimized_cost_by_interval=optimized_cost,
        baseline_vehicle_schedule=baseline_schedule,
        baseline_depot_load=baseline_depot,
        baseline_cost_by_interval=baseline_cost,
        run_id=RUN_ID,
        service_date=SERVICE_DATE,
        depot_id="DEPOT_A",
        site_import_limit_kw=None,
        exception_count=len(exceptions),
    )

    cap_run_id = f"{RUN_ID}_site_cap"
    cap_schedule, cap_depot, cap_cost, cap_exceptions = optimize_smart_charging(
        requirements,
        market_prices,
        run_id=cap_run_id,
        service_date=SERVICE_DATE,
        market="synthetic_day_ahead",
        source="synthetic",
        price_type="synthetic",
        site_import_limit_kw=750.0,
    )
    cap_summary = build_optimization_summary(
        optimized_vehicle_schedule=cap_schedule,
        optimized_depot_load=cap_depot,
        optimized_cost_by_interval=cap_cost,
        baseline_vehicle_schedule=baseline_schedule,
        baseline_depot_load=baseline_depot,
        baseline_cost_by_interval=baseline_cost,
        run_id=cap_run_id,
        service_date=SERVICE_DATE,
        depot_id="DEPOT_A",
        site_import_limit_kw=750.0,
        exception_count=len(cap_exceptions),
    )

    outputs = {
        PROCESSED_DIR / "optimized_vehicle_schedule_sample.csv": optimized_schedule,
        PROCESSED_DIR / "optimized_depot_load_sample.csv": optimized_depot,
        PROCESSED_DIR / "optimized_cost_by_interval_sample.csv": optimized_cost,
        OUTPUTS_DIR / "phase4_optimization_summary_sample.csv": summary,
        OUTPUTS_DIR / "phase4_optimization_exceptions_sample.csv": exceptions,
        PROCESSED_DIR / "optimized_depot_load_site_cap_sample.csv": cap_depot,
        OUTPUTS_DIR / "phase4_optimization_summary_site_cap_sample.csv": cap_summary,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)

    row = summary.iloc[0]
    print("Phase 4 smart-charging optimization generated")
    print(f"Vehicles: {row['vehicles_total']}")
    print(f"Optimized delivered MWh: {row['optimized_delivered_mwh']:.3f}")
    print(f"Optimized cost GBP: {row['optimized_cost_gbp']:.2f}")
    print(f"Baseline cost GBP: {row['baseline_cost_gbp']:.2f}")
    print(f"Savings GBP: {row['savings_gbp']:.2f}")
    print(f"Savings pct: {row['savings_pct']:.2f}")
    print(f"Optimized peak import kW: {row['optimized_peak_import_kw']:.2f}")
    print(f"Baseline peak import kW: {row['baseline_peak_import_kw']:.2f}")
    print(f"Readiness pct: {row['vehicle_readiness_pct']:.1f}")
    print(f"Unmet MWh: {row['total_unmet_mwh']:.6f}")
    print(f"Exceptions: {len(exceptions)}")
    for path in outputs:
        print(f"Wrote {path.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
