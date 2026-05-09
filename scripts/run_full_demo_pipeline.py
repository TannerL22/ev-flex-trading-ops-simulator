"""Run the full local demo pipeline from sample inputs to Excel report."""

from __future__ import annotations

import subprocess
import sys

from ev_flex_trading.config import PROJECT_ROOT

PIPELINE_STEPS = [
    "generate_phase1_sample_data.py",
    "generate_phase2_market_data.py",
    "generate_phase3_baseline.py",
    "generate_phase4_optimized_schedule.py",
    "generate_phase5_trading_reconciliation.py",
    "generate_phase6_excel_report.py",
    "export_dashboard_json.py",
]


def main() -> int:
    print("Running EV Flex Trading Ops demo pipeline", flush=True)
    for step in PIPELINE_STEPS:
        script = PROJECT_ROOT / "scripts" / step
        print(f"\n==> {script.relative_to(PROJECT_ROOT)}", flush=True)
        result = subprocess.run([sys.executable, str(script)], cwd=PROJECT_ROOT, check=False)
        if result.returncode != 0:
            print(f"Pipeline failed at {step} with exit code {result.returncode}", flush=True)
            return result.returncode

    print("\nFull demo pipeline completed", flush=True)
    print("React dashboard: cd frontend && npm run dev", flush=True)
    print("Streamlit dashboard: streamlit run app/streamlit_app.py", flush=True)
    print("Excel report: data/outputs/ev_flex_daily_trading_report_sample.xlsx", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
