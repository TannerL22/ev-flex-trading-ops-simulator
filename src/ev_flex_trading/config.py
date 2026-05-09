"""Project paths and shared defaults."""

from __future__ import annotations

from pathlib import Path

DEFAULT_TIMEZONE = "Europe/London"

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_INPUTS_DIR = DATA_DIR / "sample_inputs"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"


def ensure_data_directories() -> None:
    """Create standard data directories used by local sample workflows."""

    for path in (SAMPLE_INPUTS_DIR, PROCESSED_DIR, OUTPUTS_DIR):
        path.mkdir(parents=True, exist_ok=True)
