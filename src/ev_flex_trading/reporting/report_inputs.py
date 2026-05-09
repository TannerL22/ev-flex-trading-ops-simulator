"""Load report inputs from generated Phase 1-5 outputs."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass

import pandas as pd

from ev_flex_trading.config import OUTPUTS_DIR, PROCESSED_DIR, PROJECT_ROOT


@dataclass(frozen=True)
class ExcelReportInputs:
    fleet_requirements: pd.DataFrame
    market_prices: pd.DataFrame
    baseline_schedule: pd.DataFrame
    optimized_schedule: pd.DataFrame
    actual_charging: pd.DataFrame
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


REQUIRED_INPUTS = {
    "fleet_requirements": PROCESSED_DIR / "fleet_requirements_sample.csv",
    "market_prices": PROCESSED_DIR / "market_prices_synthetic_base.csv",
    "baseline_schedule": PROCESSED_DIR / "baseline_vehicle_schedule_sample.csv",
    "optimized_schedule": PROCESSED_DIR / "optimized_vehicle_schedule_sample.csv",
    "actual_charging": PROCESSED_DIR / "actual_charging_base_sample.csv",
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
}


def load_excel_report_inputs(
    *, auto_generate: bool = True
) -> tuple[ExcelReportInputs, pd.DataFrame]:
    """Load report inputs, optionally running Phase 5 generation if inputs are missing."""

    missing = [path for path in REQUIRED_INPUTS.values() if not path.exists()]
    if missing and auto_generate:
        subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "generate_phase5_trading_reconciliation.py"),
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )
        missing = [path for path in REQUIRED_INPUTS.values() if not path.exists()]
    if missing:
        missing_list = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(
            f"Missing report inputs: {missing_list}. Run scripts/generate_phase5_trading_reconciliation.py first."
        )

    frames = {name: pd.read_csv(path) for name, path in REQUIRED_INPUTS.items()}
    manifest = pd.DataFrame(
        [
            {
                "input_name": name,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "rows": len(frames[name]),
            }
            for name, path in REQUIRED_INPUTS.items()
        ]
    )
    return ExcelReportInputs(**frames), manifest
