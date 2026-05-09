"""Load and prepare dashboard data from generated sample outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ev_flex_trading.config import OUTPUTS_DIR, PROCESSED_DIR, PROJECT_ROOT
from ev_flex_trading.dashboard.formatting import (
    format_gbp as _format_gbp,
    format_kw as _format_kw,
    format_mwh as _format_mwh,
    format_pct as _format_pct,
    safe_float,
)

SCENARIO_LABELS = {
    "base_actuals": "Base actuals",
    "high_deviation": "High deviation",
}


@dataclass(frozen=True)
class DashboardFileStatus:
    """Load status for a dashboard input file."""

    name: str
    path: Path
    exists: bool
    rows: int
    required: bool = True


@dataclass(frozen=True)
class DashboardData:
    """All dataframes needed by the Streamlit dashboard."""

    fleet_requirements: pd.DataFrame
    market_prices: pd.DataFrame
    baseline_depot_load: pd.DataFrame
    baseline_cost_by_interval: pd.DataFrame
    baseline_schedule: pd.DataFrame
    optimized_depot_load: pd.DataFrame
    optimized_schedule: pd.DataFrame
    actual_charging_base: pd.DataFrame
    actual_charging_high: pd.DataFrame
    scheduled_position: pd.DataFrame
    reconciliation_base: pd.DataFrame
    reconciliation_high: pd.DataFrame
    settlement_base: pd.DataFrame
    settlement_high: pd.DataFrame
    daily_summary_base: pd.DataFrame
    daily_summary_high: pd.DataFrame
    market_metrics: pd.DataFrame
    exceptions: pd.DataFrame
    baseline_summary: pd.DataFrame
    optimization_summary_site_cap: pd.DataFrame
    report_manifest: pd.DataFrame
    file_status: pd.DataFrame


DASHBOARD_FILES = {
    "fleet_requirements": PROCESSED_DIR / "fleet_requirements_sample.csv",
    "market_prices": PROCESSED_DIR / "market_prices_synthetic_base.csv",
    "baseline_depot_load": PROCESSED_DIR / "baseline_depot_load_sample.csv",
    "baseline_cost_by_interval": PROCESSED_DIR / "baseline_cost_by_interval_sample.csv",
    "baseline_schedule": PROCESSED_DIR / "baseline_vehicle_schedule_sample.csv",
    "optimized_depot_load": PROCESSED_DIR / "optimized_depot_load_site_cap_sample.csv",
    "optimized_schedule": PROCESSED_DIR / "optimized_vehicle_schedule_sample.csv",
    "actual_charging_base": PROCESSED_DIR / "actual_charging_base_sample.csv",
    "actual_charging_high": PROCESSED_DIR / "actual_charging_high_deviation_sample.csv",
    "scheduled_position": PROCESSED_DIR / "scheduled_position_sample.csv",
    "reconciliation_base": PROCESSED_DIR / "reconciliation_base_sample.csv",
    "reconciliation_high": PROCESSED_DIR / "reconciliation_high_deviation_sample.csv",
    "settlement_base": PROCESSED_DIR / "settlement_style_exposure_base_sample.csv",
    "settlement_high": PROCESSED_DIR / "settlement_style_exposure_high_deviation_sample.csv",
    "daily_summary_base": OUTPUTS_DIR / "phase5_daily_summary_base_sample.csv",
    "daily_summary_high": OUTPUTS_DIR / "phase5_daily_summary_high_deviation_sample.csv",
    "market_metrics": OUTPUTS_DIR / "phase5_market_participation_metrics_sample.csv",
    "exceptions": OUTPUTS_DIR / "phase5_reconciliation_exceptions_sample.csv",
    "baseline_summary": OUTPUTS_DIR / "phase3_baseline_summary_sample.csv",
    "optimization_summary_site_cap": OUTPUTS_DIR
    / "phase4_optimization_summary_site_cap_sample.csv",
    "report_manifest": OUTPUTS_DIR / "phase6_report_manifest_sample.csv",
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_dashboard_data(project_root: Path | None = None) -> DashboardData:
    """Load dashboard inputs from generated CSV outputs.

    Missing files return empty dataframes and are recorded in ``file_status`` so the
    Streamlit app can show clear remediation guidance instead of failing with a stack trace.
    """

    root = project_root or PROJECT_ROOT
    frames: dict[str, pd.DataFrame] = {}
    statuses: list[DashboardFileStatus] = []

    for name, default_path in DASHBOARD_FILES.items():
        relative_path = default_path.relative_to(PROJECT_ROOT)
        path = root / relative_path
        frame = _read_csv(path)
        frames[name] = frame
        statuses.append(
            DashboardFileStatus(
                name=name,
                path=path,
                exists=path.exists(),
                rows=len(frame),
                required=name != "report_manifest",
            )
        )

    status_frame = pd.DataFrame([status.__dict__ for status in statuses])
    return DashboardData(file_status=status_frame, **frames)


def missing_required_files(data: DashboardData) -> pd.DataFrame:
    """Return missing required dashboard input files."""

    status = data.file_status
    if status.empty:
        return pd.DataFrame()
    return status[(status["required"]) & (~status["exists"])].copy()


def get_scenario_daily_summary(data: DashboardData, scenario: str) -> pd.Series:
    """Return the one-row daily summary for the requested scenario."""

    frame = data.daily_summary_high if scenario == "high_deviation" else data.daily_summary_base
    if frame.empty:
        return pd.Series(dtype="object")
    return frame.iloc[0]


def get_scenario_reconciliation(data: DashboardData, scenario: str) -> pd.DataFrame:
    """Return reconciliation dataframe for the requested scenario."""

    return data.reconciliation_high if scenario == "high_deviation" else data.reconciliation_base


def get_scenario_settlement(data: DashboardData, scenario: str) -> pd.DataFrame:
    """Return settlement-style exposure dataframe for the requested scenario."""

    return data.settlement_high if scenario == "high_deviation" else data.settlement_base


def get_scenario_actuals(data: DashboardData, scenario: str) -> pd.DataFrame:
    """Return actual charging dataframe for the requested scenario."""

    return data.actual_charging_high if scenario == "high_deviation" else data.actual_charging_base


def get_scenario_metrics(data: DashboardData, scenario: str) -> pd.Series:
    """Return market participation metrics for the requested scenario."""

    if data.market_metrics.empty or "scenario" not in data.market_metrics.columns:
        return pd.Series(dtype="object")
    match = data.market_metrics[data.market_metrics["scenario"] == scenario]
    if match.empty:
        return pd.Series(dtype="object")
    return match.iloc[0]


def prepare_baseline_optimized_load_profile(data: DashboardData) -> pd.DataFrame:
    """Prepare a wide interval load profile for baseline and site-cap optimized charging."""

    baseline = data.baseline_depot_load.copy()
    optimized = data.optimized_depot_load.copy()
    if baseline.empty or optimized.empty:
        return pd.DataFrame()

    baseline_profile = baseline[
        ["timestamp", "settlement_period", "interval_kw", "total_charge_mwh"]
    ].rename(
        columns={
            "interval_kw": "baseline_kw",
            "total_charge_mwh": "baseline_mwh",
        }
    )
    optimized_profile = optimized[
        ["timestamp", "settlement_period", "interval_kw", "total_charge_mwh"]
    ].rename(
        columns={
            "interval_kw": "optimized_kw",
            "total_charge_mwh": "optimized_mwh",
        }
    )
    profile = pd.merge(
        baseline_profile,
        optimized_profile,
        on=["timestamp", "settlement_period"],
        how="outer",
    ).fillna(0)

    if not data.market_prices.empty:
        prices = data.market_prices[["settlement_period", "price_gbp_per_mwh"]].drop_duplicates()
        profile = profile.merge(prices, on="settlement_period", how="left")
    return profile.sort_values("settlement_period").reset_index(drop=True)


def prepare_reconciliation_profile(data: DashboardData, scenario: str) -> pd.DataFrame:
    """Prepare scheduled, actual, and deviation series for charting."""

    reconciliation = get_scenario_reconciliation(data, scenario).copy()
    if reconciliation.empty:
        return pd.DataFrame()
    columns = [
        "timestamp",
        "settlement_period",
        "scheduled_mwh",
        "actual_mwh",
        "deviation_mwh",
        "reconciliation_status",
    ]
    return reconciliation[
        [column for column in columns if column in reconciliation.columns]
    ].sort_values("settlement_period")


def prepare_cost_comparison(data: DashboardData, scenario: str) -> pd.DataFrame:
    """Prepare baseline, optimized plan, and realized cost comparison."""

    summary = get_scenario_daily_summary(data, scenario)
    if summary.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "cost_type": "Dumb baseline cost",
                "cost_gbp": _numeric(summary.get("dumb_baseline_cost_gbp")),
            },
            {
                "cost_type": "Optimized expected cost",
                "cost_gbp": _numeric(summary.get("optimized_expected_cost_gbp")),
            },
            {
                "cost_type": "Settlement-style actual cost",
                "cost_gbp": _numeric(summary.get("total_settlement_style_cost_gbp")),
            },
        ]
    )


def prepare_exception_summary(exceptions: pd.DataFrame, by: str) -> pd.DataFrame:
    """Summarize exceptions by severity or category."""

    if exceptions.empty or by not in exceptions.columns:
        return pd.DataFrame(columns=[by, "count"])
    return exceptions.groupby(by, dropna=False).size().reset_index(name="count")


def _numeric(value: object, default: float = 0.0) -> float:
    return safe_float(value, default)


def format_currency(value: object) -> str:
    """Format a dashboard GBP value."""

    return _format_gbp(value)


def format_mwh(value: object) -> str:
    """Format a dashboard MWh value."""

    return _format_mwh(value)


def format_kw(value: object) -> str:
    """Format a dashboard kW value."""

    return _format_kw(value)


def format_pct(value: object) -> str:
    """Format percentage values stored as either percent points or fractions."""

    return _format_pct(value)
