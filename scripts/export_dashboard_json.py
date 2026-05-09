"""Export generated workflow outputs as static JSON for the React dashboard."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from ev_flex_trading.config import OUTPUTS_DIR, PROCESSED_DIR, PROJECT_ROOT
from ev_flex_trading.dashboard.data_loader import (
    get_scenario_daily_summary,
    get_scenario_metrics,
    load_dashboard_data,
    prepare_baseline_optimized_load_profile,
    prepare_cost_comparison,
    prepare_exception_summary,
    prepare_reconciliation_profile,
)

FRONTEND_PUBLIC_DATA = PROJECT_ROOT / "frontend" / "public" / "data"
FRONTEND_PUBLIC_REPORTS = PROJECT_ROOT / "frontend" / "public" / "reports"
DEFAULT_OUTPUT = FRONTEND_PUBLIC_DATA / "dashboard.json"
EXCEL_REPORT_NAME = "ev_flex_daily_trading_report_sample.xlsx"


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    clean = frame.astype("object").where(pd.notna(frame), None)
    return [_clean_json_value(record) for record in clean.to_dict(orient="records")]


def _series(series: pd.Series) -> dict[str, Any]:
    if series.empty:
        return {}
    clean = series.astype("object").where(pd.notna(series), None)
    return _clean_json_value(clean.to_dict())


def _clean_json_value(value: Any) -> Any:
    """Recursively convert pandas/numpy missing values to strict JSON null."""

    if isinstance(value, dict):
        return {key: _clean_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_json_value(item) for item in value]
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def build_dashboard_payload() -> dict[str, Any]:
    """Build a static, public-safe dashboard payload from existing outputs."""

    data = load_dashboard_data()
    exceptions_by_severity = prepare_exception_summary(data.exceptions, "severity")
    exceptions_by_category = prepare_exception_summary(data.exceptions, "category")

    scenarios = {}
    for scenario in ("base_actuals", "high_deviation"):
        scenarios[scenario] = {
            "dailySummary": _series(get_scenario_daily_summary(data, scenario)),
            "marketMetrics": _series(get_scenario_metrics(data, scenario)),
            "reconciliation": _records(prepare_reconciliation_profile(data, scenario)),
            "settlementExposure": _records(
                data.settlement_high if scenario == "high_deviation" else data.settlement_base
            ),
            "costComparison": _records(prepare_cost_comparison(data, scenario)),
        }

    payload = {
        "metadata": {
            "projectName": "EV Flex Trading Ops Simulator",
            "dataStatus": "Synthetic/sample data",
            "disclaimer": (
                "Public demonstration using synthetic/sample data. Not a production trading, "
                "dispatch, or official settlement system."
            ),
            "defaultScenario": "base_actuals",
            "excelReportPath": "data/outputs/ev_flex_daily_trading_report_sample.xlsx",
            "excelReportUrl": f"/reports/{EXCEL_REPORT_NAME}",
            "generatedFrom": "scripts/export_dashboard_json.py",
        },
        "fleetRequirements": _records(data.fleet_requirements),
        "marketPrices": _records(data.market_prices),
        "baselineOptimizedLoad": _records(prepare_baseline_optimized_load_profile(data)),
        "baselineSchedule": _records(data.baseline_schedule),
        "optimizedSchedule": _records(data.optimized_schedule),
        "actualCharging": {
            "base_actuals": _records(data.actual_charging_base),
            "high_deviation": _records(data.actual_charging_high),
        },
        "scheduledPosition": _records(data.scheduled_position),
        "exceptions": _records(data.exceptions),
        "exceptionsBySeverity": _records(exceptions_by_severity),
        "exceptionsByCategory": _records(exceptions_by_category),
        "baselineSummary": _records(data.baseline_summary),
        "optimizationSummarySiteCap": _records(data.optimization_summary_site_cap),
        "scenarios": scenarios,
    }
    return payload


def export_dashboard_json(output_path: Path = DEFAULT_OUTPUT) -> Path:
    """Write the React dashboard payload to a static JSON file."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_PUBLIC_REPORTS.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload()
    output_path.write_text(
        json.dumps(payload, indent=2, default=str, allow_nan=False),
        encoding="utf-8",
    )
    excel_source = OUTPUTS_DIR / EXCEL_REPORT_NAME
    if excel_source.exists():
        shutil.copy2(excel_source, FRONTEND_PUBLIC_REPORTS / EXCEL_REPORT_NAME)
    return output_path


def main() -> int:
    output_path = export_dashboard_json()
    print(f"Dashboard JSON exported: {output_path.relative_to(PROJECT_ROOT)}")
    print(f"Rows: fleet={len(pd.read_csv(PROCESSED_DIR / 'fleet_requirements_sample.csv'))}")
    print(f"Excel report reference: data/outputs/{EXCEL_REPORT_NAME}")
    print(f"Frontend report copy: frontend/public/reports/{EXCEL_REPORT_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
