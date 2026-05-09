"""Generate the Phase 6 Excel daily trading report."""

from __future__ import annotations

from pathlib import Path

from ev_flex_trading.config import PROJECT_ROOT
from ev_flex_trading.reporting.excel_report import generate_excel_report


def main() -> int:
    workbook_path, manifest = generate_excel_report(auto_generate_inputs=True)
    print("Phase 6 Excel daily trading report generated")
    print(f"Workbook: {workbook_path.relative_to(PROJECT_ROOT)}")
    print(f"Manifest rows: {len(manifest)}")
    print("Sheets: README, Daily Summary, Baseline vs Optimized, Scheduled vs Actual,")
    print("        Settlement Exposure, Market Metrics, Exceptions, Fleet Requirements,")
    print(
        "        Market Prices, Baseline Schedule, Optimized Schedule, Actual Charging, Assumptions"
    )
    print(f"Wrote {Path(workbook_path).relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
