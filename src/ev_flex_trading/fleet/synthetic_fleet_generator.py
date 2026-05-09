"""Synthetic EV fleet schedule generation for public sample data."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from ev_flex_trading.config import DEFAULT_TIMEZONE, SAMPLE_INPUTS_DIR, ensure_data_directories

VEHICLE_TYPE_DISTRIBUTION = {
    "single_deck_bus": 0.55,
    "double_deck_bus": 0.30,
    "commercial_van": 0.15,
}

BATTERY_RANGES_KWH = {
    "single_deck_bus": (280, 390),
    "double_deck_bus": (360, 520),
    "commercial_van": (75, 130),
}

CHARGER_OPTIONS_KW = {
    "single_deck_bus": [75, 100, 150],
    "double_deck_bus": [100, 150],
    "commercial_van": [50, 75],
}


def _local_timestamp(service_date: date, hour_float: float) -> pd.Timestamp:
    whole_hours = int(hour_float)
    minutes = int(round((hour_float - whole_hours) * 60 / 5) * 5)
    day_offset = whole_hours // 24
    hour = whole_hours % 24
    timestamp = datetime.combine(service_date + timedelta(days=day_offset), datetime.min.time())
    return pd.Timestamp(timestamp + timedelta(hours=hour, minutes=minutes), tz=DEFAULT_TIMEZONE)


def generate_synthetic_fleet_schedule(
    *,
    service_date: date | str,
    depot_id: str = "DEPOT_A",
    n_vehicles: int = 24,
    random_seed: int = 42,
    vehicle_type_distribution: dict[str, float] | None = None,
    arrival_window: tuple[float, float] = (18.0, 24.5),
    departure_window: tuple[float, float] = (28.5, 32.0),
    start_soc_range: tuple[float, float] = (18.0, 55.0),
    target_soc_range: tuple[float, float] = (80.0, 95.0),
) -> pd.DataFrame:
    """Generate a plausible depot EV fleet schedule.

    Defaults model an overnight bus/commercial fleet depot: most vehicles arrive
    in the evening and leave early the next morning. Times beyond 24 represent
    the following local day, so a departure window of 28.5-32.0 maps to
    04:30-08:00 next day.
    """

    local_date = date.fromisoformat(service_date) if isinstance(service_date, str) else service_date
    rng = np.random.default_rng(random_seed)
    distribution = vehicle_type_distribution or VEHICLE_TYPE_DISTRIBUTION
    vehicle_types = list(distribution)
    probabilities = np.array(list(distribution.values()), dtype=float)
    probabilities = probabilities / probabilities.sum()

    records = []
    for index in range(1, n_vehicles + 1):
        vehicle_type = str(rng.choice(vehicle_types, p=probabilities))
        battery_low, battery_high = BATTERY_RANGES_KWH[vehicle_type]
        arrival_hour = float(rng.uniform(*arrival_window))
        departure_hour = float(rng.uniform(*departure_window))
        start_soc = float(rng.uniform(*start_soc_range))
        target_soc = float(rng.uniform(max(target_soc_range[0], start_soc), target_soc_range[1]))
        charger_kw = int(rng.choice(CHARGER_OPTIONS_KW[vehicle_type]))
        priority = str(rng.choice(["high", "normal", "low"], p=[0.2, 0.65, 0.15]))

        records.append(
            {
                "service_date": local_date.isoformat(),
                "depot_id": depot_id,
                "vehicle_id": f"{depot_id}-EV-{index:03d}",
                "vehicle_type": vehicle_type,
                "arrival_time": _local_timestamp(local_date, arrival_hour).isoformat(),
                "departure_time": _local_timestamp(local_date, departure_hour).isoformat(),
                "battery_kwh": round(float(rng.uniform(battery_low, battery_high)), 1),
                "start_soc_pct": round(start_soc, 1),
                "target_soc_pct": round(target_soc, 1),
                "max_charger_kw": charger_kw,
                "assigned_charger_id": f"{depot_id}-CHG-{((index - 1) % max(1, n_vehicles // 3)) + 1:02d}",
                "priority": priority,
                "route_block": f"RB-{rng.integers(100, 999)}",
            }
        )

    return pd.DataFrame.from_records(records)


def write_sample_fleet_schedule(
    *,
    service_date: date | str = "2026-05-09",
    depot_id: str = "DEPOT_A",
    n_vehicles: int = 24,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Generate and write the Phase 1 sample fleet schedule CSV."""

    ensure_data_directories()
    frame = generate_synthetic_fleet_schedule(
        service_date=service_date,
        depot_id=depot_id,
        n_vehicles=n_vehicles,
        random_seed=random_seed,
    )
    frame.to_csv(SAMPLE_INPUTS_DIR / "ev_fleet_schedule_sample.csv", index=False)
    return frame
