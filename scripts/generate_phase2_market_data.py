"""Generate Phase 2 sample market data and normalized outputs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from ev_flex_trading.config import (
    OUTPUTS_DIR,
    PROCESSED_DIR,
    SAMPLE_INPUTS_DIR,
    ensure_data_directories,
)
from ev_flex_trading.ingestion.epex_csv_loader import load_epex_style_csv
from ev_flex_trading.ingestion.synthetic_market_generator import generate_synthetic_market_prices
from ev_flex_trading.validation.exceptions import exceptions_frame

SERVICE_DATE = "2026-05-09"


def _write_epex_style_sample(path: Path, market: str, seed: int, price_shift: float = 0.0) -> None:
    synthetic = generate_synthetic_market_prices(
        service_date=SERVICE_DATE,
        random_seed=seed,
        base_price=78.0 + price_shift,
        market=market,
        source="sample_epex_csv",
        scenario="base",
    )
    sample = pd.DataFrame(
        {
            "delivery_date": synthetic["settlement_date"],
            "settlement_period": synthetic["settlement_period"],
            "delivery_start": synthetic["timestamp"],
            "delivery_end": pd.to_datetime(synthetic["timestamp"]) + pd.Timedelta(minutes=30),
            "price_gbp_per_mwh": synthetic["price_gbp_per_mwh"],
            "market": market,
            "source": "sample_epex_csv",
            "price_type": "auction_clearing",
            "currency": "GBP",
            "unit": "MWh",
            "notes": "Synthetic EPEX-style sample file; not official EPEX data.",
        }
    )
    sample.to_csv(path, index=False)


def main() -> int:
    ensure_data_directories()

    generated = {
        "synthetic_base": generate_synthetic_market_prices(
            service_date=SERVICE_DATE,
            random_seed=100,
            scenario="base",
            market="synthetic_day_ahead",
        ),
        "synthetic_evening_spike": generate_synthetic_market_prices(
            service_date=SERVICE_DATE,
            random_seed=101,
            scenario="evening_spike",
            market="synthetic_day_ahead",
        ),
        "synthetic_negative_overnight": generate_synthetic_market_prices(
            service_date=SERVICE_DATE,
            random_seed=102,
            scenario="negative_price_overnight",
            market="synthetic_day_ahead",
        ),
    }

    output_paths = []
    for name, frame in generated.items():
        path = PROCESSED_DIR / f"market_prices_{name}.csv"
        frame.to_csv(path, index=False)
        output_paths.append(path)

    day_ahead_path = SAMPLE_INPUTS_DIR / "epex_day_ahead_sample.csv"
    intraday_path = SAMPLE_INPUTS_DIR / "epex_intraday_sample.csv"
    _write_epex_style_sample(day_ahead_path, "day_ahead", seed=110)
    _write_epex_style_sample(intraday_path, "intraday", seed=111, price_shift=3.5)

    epex_outputs = {
        "epex_day_ahead_sample": load_epex_style_csv(
            day_ahead_path,
            service_date=SERVICE_DATE,
            default_market="day_ahead",
            run_id="phase2_epex_day_ahead",
        ),
        "epex_intraday_sample": load_epex_style_csv(
            intraday_path,
            service_date=SERVICE_DATE,
            default_market="intraday",
            run_id="phase2_epex_intraday",
        ),
    }

    exception_frames = []
    for name, (frame, exceptions) in epex_outputs.items():
        path = PROCESSED_DIR / f"market_prices_{name}.csv"
        frame.to_csv(path, index=False)
        output_paths.append(path)
        exception_frames.append(exceptions)

    all_exceptions = (
        pd.concat(exception_frames, ignore_index=True) if exception_frames else exceptions_frame()
    )
    exceptions_path = OUTPUTS_DIR / "phase2_market_exceptions_sample.csv"
    all_exceptions.to_csv(exceptions_path, index=False)
    output_paths.append(exceptions_path)

    severity_counts = Counter(all_exceptions["severity"]) if not all_exceptions.empty else Counter()
    print("Phase 2 market data generated")
    print(f"Service date: {SERVICE_DATE}")
    print(f"Synthetic rows generated: {sum(len(frame) for frame in generated.values())}")
    print(f"EPEX-style rows loaded: {sum(len(frame) for frame, _ in epex_outputs.values())}")
    print(f"Exceptions by severity: {dict(severity_counts)}")
    for path in output_paths:
        print(f"Wrote {path.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
