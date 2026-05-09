from __future__ import annotations

from pathlib import Path

import pandas as pd

from ev_flex_trading.dashboard.charts import (
    build_baseline_vs_optimized_chart,
    build_cost_comparison_chart,
    build_scheduled_vs_actual_chart,
    build_settlement_exposure_chart,
)
from ev_flex_trading.dashboard.components import kpi_card_html, summary_list_html
from ev_flex_trading.dashboard.data_loader import (
    format_currency,
    format_mwh,
    format_pct,
    get_scenario_daily_summary,
    load_dashboard_data,
    missing_required_files,
    prepare_baseline_optimized_load_profile,
    prepare_cost_comparison,
    prepare_reconciliation_profile,
)
from ev_flex_trading.dashboard.formatting import (
    format_gbp,
    format_gbp_per_mwh,
    format_integer,
    format_kw,
    safe_float,
    safe_int,
)


def test_dashboard_data_loads_generated_outputs() -> None:
    data = load_dashboard_data()

    assert not data.daily_summary_base.empty
    assert not data.daily_summary_high.empty
    assert not data.market_prices.empty
    assert missing_required_files(data).empty


def test_missing_dashboard_files_return_helpful_status(tmp_path: Path) -> None:
    data = load_dashboard_data(project_root=tmp_path)
    missing = missing_required_files(data)

    assert not missing.empty
    assert {"name", "path", "exists", "required"}.issubset(missing.columns)
    assert missing["exists"].eq(False).all()


def test_scenario_daily_summary_selection() -> None:
    data = load_dashboard_data()

    base = get_scenario_daily_summary(data, "base_actuals")
    high = get_scenario_daily_summary(data, "high_deviation")

    assert base["scenario"] == "base_actuals"
    assert high["scenario"] == "high_deviation"
    assert float(high["exception_count"]) >= float(base["exception_count"])


def test_chart_prep_outputs_expected_columns() -> None:
    data = load_dashboard_data()

    load_profile = prepare_baseline_optimized_load_profile(data)
    reconciliation = prepare_reconciliation_profile(data, "base_actuals")
    cost_comparison = prepare_cost_comparison(data, "base_actuals")

    assert {
        "settlement_period",
        "baseline_kw",
        "optimized_kw",
        "price_gbp_per_mwh",
    }.issubset(load_profile.columns)
    assert {"scheduled_mwh", "actual_mwh", "deviation_mwh"}.issubset(reconciliation.columns)
    assert list(cost_comparison.columns) == ["cost_type", "cost_gbp"]
    assert len(cost_comparison) == 3


def test_kpi_formatting_helpers() -> None:
    assert format_currency(237.414) == "£237.41"
    assert format_gbp(237.414) == "£237.41"
    assert format_gbp_per_mwh(51.9) == "£51.90/MWh"
    assert format_mwh(4.56529) == "4.565 MWh"
    assert format_kw(750) == "750.0 kW"
    assert format_integer(24) == "24"
    assert format_pct(36.5539) == "36.6%"
    assert format_pct(0.365539) == "36.6%"
    assert safe_float("bad", 1.5) == 1.5
    assert safe_int("4.4") == 4


def test_cost_comparison_uses_selected_scenario() -> None:
    data = load_dashboard_data()

    base = prepare_cost_comparison(data, "base_actuals")
    high = prepare_cost_comparison(data, "high_deviation")

    base_realized = float(
        base.loc[base["cost_type"] == "Settlement-style actual cost", "cost_gbp"].iloc[0]
    )
    high_realized = float(
        high.loc[high["cost_type"] == "Settlement-style actual cost", "cost_gbp"].iloc[0]
    )
    assert base_realized != high_realized


def test_empty_project_root_returns_empty_frames(tmp_path: Path) -> None:
    data = load_dashboard_data(project_root=tmp_path)

    assert data.daily_summary_base.empty
    assert data.reconciliation_base.empty
    assert isinstance(data.file_status, pd.DataFrame)


def test_dashboard_chart_builders_return_figures() -> None:
    data = load_dashboard_data()
    load_profile = prepare_baseline_optimized_load_profile(data)
    reconciliation = prepare_reconciliation_profile(data, "base_actuals")
    costs = prepare_cost_comparison(data, "base_actuals")

    assert build_baseline_vs_optimized_chart(load_profile).data
    assert build_scheduled_vs_actual_chart(reconciliation).data
    assert build_settlement_exposure_chart(data.settlement_base).data
    assert build_cost_comparison_chart(costs).data


def test_component_html_helpers_escape_and_render_expected_markup() -> None:
    kpi = kpi_card_html(
        title="Scheduled <MWh>",
        value="4.565 MWh",
        subtext="Scheduled position",
        icon="MWh",
    )
    summary = summary_list_html([("Vehicles", "24")])

    assert "ev-kpi-card" in kpi
    assert "Scheduled &lt;MWh&gt;" in kpi
    assert "ev-summary-row" in summary
