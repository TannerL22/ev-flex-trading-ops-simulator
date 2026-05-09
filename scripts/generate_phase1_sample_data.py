"""Generate Phase 1 sample fleet data and validation outputs."""

from __future__ import annotations

from ev_flex_trading.config import OUTPUTS_DIR, PROCESSED_DIR, ensure_data_directories
from ev_flex_trading.fleet.fleet_requirements import calculate_fleet_requirements
from ev_flex_trading.fleet.synthetic_fleet_generator import write_sample_fleet_schedule
from ev_flex_trading.validation.data_quality_checks import check_fleet_schedule_quality


def main() -> int:
    ensure_data_directories()
    fleet = write_sample_fleet_schedule()
    exceptions = check_fleet_schedule_quality(fleet, run_id="phase1_sample")
    requirements = calculate_fleet_requirements(fleet)

    requirements.to_csv(PROCESSED_DIR / "fleet_requirements_sample.csv", index=False)
    exceptions.to_csv(OUTPUTS_DIR / "phase1_exceptions_sample.csv", index=False)

    feasible_count = int(requirements["feasibility_flag"].eq("feasible").sum())
    print("Phase 1 sample data generated")
    print(f"Vehicles: {len(fleet)}")
    print(f"Feasible vehicles: {feasible_count}")
    print(f"Exceptions: {len(exceptions)}")
    print("Wrote data/sample_inputs/ev_fleet_schedule_sample.csv")
    print("Wrote data/processed/fleet_requirements_sample.csv")
    print("Wrote data/outputs/phase1_exceptions_sample.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
