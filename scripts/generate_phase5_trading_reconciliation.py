"""Generate Phase 5 actuals, reconciliation, and settlement-style outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ev_flex_trading.actuals.actual_charging_simulator import simulate_actual_charging
from ev_flex_trading.actuals.actuals_reconciliation import reconcile_scheduled_vs_actual
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
from ev_flex_trading.trading.market_metrics import calculate_market_participation_metrics
from ev_flex_trading.trading.optimization_comparison import build_optimization_summary
from ev_flex_trading.trading.pnl_report import build_daily_pnl_style_summary
from ev_flex_trading.trading.position_builder import build_scheduled_position
from ev_flex_trading.trading.settlement_simulator import simulate_settlement_style_exposure
from ev_flex_trading.validation.exceptions import exceptions_frame

SERVICE_DATE = "2026-05-09"
RUN_ID = "phase5_trading_reconciliation_sample"
SITE_CAP_KW = 750.0


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
            random_seed=500 + index,
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

    baseline_schedule, baseline_exceptions = build_dumb_charging_baseline(
        requirements, run_id=RUN_ID
    )
    baseline_depot = aggregate_depot_load(baseline_schedule, run_id=RUN_ID)
    market_prices = _ensure_market_prices_cover_dates(
        market_prices,
        set(baseline_depot["settlement_date"].astype(str)),
    )
    baseline_cost, _, baseline_cost_exceptions = calculate_baseline_charging_cost(
        baseline_depot,
        market_prices,
        vehicle_schedule=baseline_schedule,
        market="synthetic_day_ahead",
        source="synthetic",
        price_type="synthetic",
        run_id=RUN_ID,
    )

    optimized_schedule, optimized_depot, optimized_cost, opt_exceptions = optimize_smart_charging(
        requirements,
        market_prices,
        run_id=RUN_ID,
        service_date=SERVICE_DATE,
        market="synthetic_day_ahead",
        source="synthetic",
        price_type="synthetic",
        site_import_limit_kw=SITE_CAP_KW,
    )
    optimized_summary = build_optimization_summary(
        optimized_vehicle_schedule=optimized_schedule,
        optimized_depot_load=optimized_depot,
        optimized_cost_by_interval=optimized_cost,
        baseline_vehicle_schedule=baseline_schedule,
        baseline_depot_load=baseline_depot,
        baseline_cost_by_interval=baseline_cost,
        run_id=RUN_ID,
        service_date=SERVICE_DATE,
        depot_id="DEPOT_A",
        site_import_limit_kw=SITE_CAP_KW,
        exception_count=len(opt_exceptions),
    )

    position = build_scheduled_position(
        optimized_schedule,
        run_id=RUN_ID,
        position_type="site_cap_optimized_schedule",
    )

    scenario_outputs = {}
    all_exceptions = [baseline_exceptions, baseline_cost_exceptions, opt_exceptions]
    metrics_frames = []
    for scenario, seed in [("base_actuals", 700), ("high_deviation", 701)]:
        actuals = simulate_actual_charging(
            optimized_schedule,
            run_id=RUN_ID,
            random_seed=seed,
            scenario=scenario,
        )
        reconciliation, rec_exceptions = reconcile_scheduled_vs_actual(
            position,
            actuals,
            run_id=RUN_ID,
        )
        settlement, settlement_exceptions = simulate_settlement_style_exposure(
            reconciliation,
            market_prices,
            run_id=RUN_ID,
        )
        scenario_exceptions = pd.concat(
            [rec_exceptions, settlement_exceptions],
            ignore_index=True,
        )
        daily_summary = build_daily_pnl_style_summary(
            settlement,
            baseline_summary=optimized_summary.rename(
                columns={"baseline_cost_gbp": "baseline_cost_gbp"}
            ),
            optimized_summary=optimized_summary,
            reconciliation=reconciliation,
            exceptions=scenario_exceptions,
            run_id=RUN_ID,
            scenario=scenario,
        )
        metrics = calculate_market_participation_metrics(
            reconciliation,
            market_prices,
            run_id=RUN_ID,
            scenario=scenario,
        )
        metrics_frames.append(metrics)
        all_exceptions.append(scenario_exceptions)
        scenario_outputs[scenario] = {
            "actuals": actuals,
            "reconciliation": reconciliation,
            "settlement": settlement,
            "daily_summary": daily_summary,
        }

    exceptions = (
        pd.concat(all_exceptions, ignore_index=True) if all_exceptions else exceptions_frame()
    )
    metrics = pd.concat(metrics_frames, ignore_index=True)

    outputs = {
        PROCESSED_DIR
        / "actual_charging_base_sample.csv": scenario_outputs["base_actuals"]["actuals"],
        PROCESSED_DIR
        / "actual_charging_high_deviation_sample.csv": scenario_outputs["high_deviation"][
            "actuals"
        ],
        PROCESSED_DIR / "scheduled_position_sample.csv": position,
        PROCESSED_DIR
        / "reconciliation_base_sample.csv": scenario_outputs["base_actuals"]["reconciliation"],
        PROCESSED_DIR
        / "reconciliation_high_deviation_sample.csv": scenario_outputs["high_deviation"][
            "reconciliation"
        ],
        PROCESSED_DIR
        / "settlement_style_exposure_base_sample.csv": scenario_outputs["base_actuals"][
            "settlement"
        ],
        PROCESSED_DIR
        / "settlement_style_exposure_high_deviation_sample.csv": scenario_outputs["high_deviation"][
            "settlement"
        ],
        OUTPUTS_DIR
        / "phase5_daily_summary_base_sample.csv": scenario_outputs["base_actuals"]["daily_summary"],
        OUTPUTS_DIR
        / "phase5_daily_summary_high_deviation_sample.csv": scenario_outputs["high_deviation"][
            "daily_summary"
        ],
        OUTPUTS_DIR / "phase5_market_participation_metrics_sample.csv": metrics,
        OUTPUTS_DIR / "phase5_reconciliation_exceptions_sample.csv": exceptions,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)

    for scenario in ["base_actuals", "high_deviation"]:
        summary = scenario_outputs[scenario]["daily_summary"].iloc[0]
        print(f"Scenario: {scenario}")
        print(f"  Scheduled MWh: {summary['scheduled_mwh']:.3f}")
        print(f"  Actual MWh: {summary['actual_mwh']:.3f}")
        print(f"  Deviation MWh: {summary['deviation_mwh']:.3f}")
        print(f"  Settlement-style cost GBP: {summary['total_settlement_style_cost_gbp']:.2f}")
        print(
            f"  Realized savings vs baseline GBP: {summary['realized_savings_vs_baseline_gbp']:.2f}"
        )
        print(f"  Delta vs optimized plan GBP: {summary['delta_vs_optimized_plan_gbp']:.2f}")
        print(f"  Material deviation intervals: {summary['material_deviation_intervals']}")
        print(f"  Missing meter intervals: {summary['missing_meter_intervals']}")
    print(f"Exceptions: {len(exceptions)}")
    for path in outputs:
        print(f"Wrote {_display_path(path)}")
    return 0


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
