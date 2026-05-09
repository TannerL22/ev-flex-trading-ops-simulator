"""Shared result containers for optimization workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class OptimizationResult:
    vehicle_schedule: pd.DataFrame
    depot_load: pd.DataFrame
    cost_by_interval: pd.DataFrame
    summary: pd.DataFrame
    exceptions: pd.DataFrame
