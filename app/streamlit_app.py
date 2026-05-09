"""Streamlit dashboard for the EV Flex Trading Ops Simulator."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ev_flex_trading.dashboard.charts import (  # noqa: E402
    apply_dashboard_layout,
    build_baseline_vs_optimized_chart,
    build_cost_comparison_chart,
    build_exceptions_by_severity_chart,
    build_scheduled_vs_actual_chart,
    build_settlement_exposure_chart,
)
from ev_flex_trading.dashboard.components import (  # noqa: E402
    render_disclaimer_bar,
    render_download_card,
    render_empty_exceptions_state,
    render_info_badge,
    render_kpi_card,
    render_panel_header,
    render_sidebar_brand,
    render_summary_list,
)
from ev_flex_trading.dashboard.data_loader import (  # noqa: E402
    SCENARIO_LABELS,
    get_scenario_actuals,
    get_scenario_daily_summary,
    get_scenario_metrics,
    get_scenario_reconciliation,
    get_scenario_settlement,
    load_dashboard_data,
    missing_required_files,
    prepare_baseline_optimized_load_profile,
    prepare_cost_comparison,
    prepare_exception_summary,
    prepare_reconciliation_profile,
)
from ev_flex_trading.dashboard.formatting import (  # noqa: E402
    format_gbp,
    format_gbp_per_mwh,
    format_integer,
    format_kw,
    format_mwh,
    format_pct,
    safe_float,
    safe_int,
)
from ev_flex_trading.dashboard.theme import COLORS, dashboard_css  # noqa: E402

DISCLAIMER = (
    "Public demonstration using synthetic/sample data. Not a production trading, dispatch, "
    "or official settlement system."
)

NAV_ITEMS = {
    "Overview": "Overview",
    "Fleet & Market Inputs": "Fleet & Market Inputs",
    "Baseline vs Optimized": "Baseline vs Optimized",
    "Scheduled vs Actual": "Scheduled vs Actual",
    "Settlement Exposure": "Settlement Exposure",
    "Exceptions": "Exceptions",
    "Data Tables / Downloads": "Data Tables / Downloads",
    "Methodology & Limitations": "Methodology & Limitations",
}


st.set_page_config(
    page_title="EV Flex Trading Ops Simulator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(dashboard_css(), unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _load_data():
    return load_dashboard_data()


def _service_date(data_frame: pd.DataFrame) -> date:
    if data_frame.empty or "service_date" not in data_frame.columns:
        return date(2026, 5, 9)
    return pd.to_datetime(data_frame["service_date"].iloc[0]).date()


def _scenario_summary_text(summary: pd.Series) -> str:
    if summary.empty:
        return "Scenario data unavailable."
    scheduled = safe_float(summary.get("scheduled_mwh"))
    actual = safe_float(summary.get("actual_mwh"))
    if scheduled <= 0:
        return "Schedule unavailable."
    tracking = actual / scheduled
    return f"Tracking performance: {tracking * 100:,.1f}% of schedule"


def _render_topbar(selected_scenario: str, report_date: date) -> tuple[str, date]:
    with st.container():
        st.markdown('<div class="ev-topbar">', unsafe_allow_html=True)
        left, scenario_col, date_col, badge_col = st.columns([5, 2, 2, 2])
        with left:
            st.markdown(
                """
<div class="ev-page-title">EV Flex Trading Ops Simulator</div>
<div class="ev-page-subtitle">EV flexibility trading analytics, reconciliation, and reporting workflow</div>
""",
                unsafe_allow_html=True,
            )
        with scenario_col:
            scenario = st.selectbox(
                "Scenario",
                options=["base_actuals", "high_deviation"],
                index=0 if selected_scenario == "base_actuals" else 1,
                format_func=lambda value: SCENARIO_LABELS.get(value, value),
            )
        with date_col:
            selected_date = st.date_input("Report date", value=report_date)
        with badge_col:
            st.write("")
            render_info_badge("Synthetic / sample data")
        st.markdown("</div>", unsafe_allow_html=True)
    return scenario, selected_date


def _render_kpi_strip(summary: pd.Series) -> None:
    cols = st.columns(8)
    exception_count = safe_int(summary.get("material_deviation_intervals"))
    kpis = [
        (
            "Scheduled MWh",
            format_mwh(summary.get("scheduled_mwh")),
            "Scheduled position",
            "MWh",
            COLORS["blue"],
        ),
        (
            "Actual MWh",
            format_mwh(summary.get("actual_mwh")),
            _scenario_summary_text(summary),
            "ACT",
            COLORS["teal"],
        ),
        (
            "Settlement-style Cost",
            format_gbp(summary.get("total_settlement_style_cost_gbp")),
            "Simplified exposure",
            "GBP",
            COLORS["purple"],
        ),
        (
            "Dumb Baseline Cost",
            format_gbp(summary.get("dumb_baseline_cost_gbp")),
            "Immediate charging",
            "BASE",
            COLORS["orange"],
        ),
        (
            "Optimized Expected Cost",
            format_gbp(summary.get("optimized_expected_cost_gbp")),
            "Site-cap optimized",
            "OPT",
            COLORS["teal"],
        ),
        (
            "Realized Savings",
            format_gbp(summary.get("realized_savings_vs_baseline_gbp")),
            format_pct(summary.get("realized_savings_vs_baseline_pct")),
            "SAVE",
            COLORS["green"],
        ),
        (
            "Vehicle Readiness",
            format_pct(summary.get("vehicle_readiness_pct")),
            "On target",
            "READY",
            COLORS["blue"],
        ),
        (
            "Exceptions",
            format_integer(exception_count),
            "Material deviations",
            "EXC",
            COLORS["amber"] if exception_count else COLORS["green"],
        ),
    ]
    for column, (title, value, subtext, icon, color) in zip(cols, kpis, strict=True):
        with column:
            render_kpi_card(
                title=title,
                value=value,
                subtext=subtext,
                icon=icon,
                accent_color=color,
            )


def _fleet_summary_items(data, metrics: pd.Series) -> list[tuple[str, str]]:
    fleet = data.fleet_requirements
    optimization = data.optimization_summary_site_cap
    market_label = "Synthetic day-ahead"
    if not data.market_prices.empty and "market" in data.market_prices.columns:
        market_label = str(data.market_prices["market"].iloc[0]).replace("_", " ").title()
    site_cap = ""
    if not optimization.empty:
        site_cap = format_kw(optimization.iloc[0].get("site_import_limit_kw"))
    return [
        ("Number of vehicles", format_integer(len(fleet))),
        (
            "Total required energy",
            format_mwh(fleet["required_kwh"].sum() / 1000 if not fleet.empty else 0),
        ),
        ("Average start SoC", format_pct(fleet["start_soc_pct"].mean() if not fleet.empty else 0)),
        (
            "Average target SoC",
            format_pct(fleet["target_soc_pct"].mean() if not fleet.empty else 0),
        ),
        ("Site import cap", site_cap or "Not available"),
        ("Active settlement periods", format_integer(metrics.get("active_settlement_periods"))),
        ("Market", market_label),
    ]


def _render_missing_inputs(missing: pd.DataFrame) -> None:
    if missing.empty:
        return
    st.warning(
        "Required sample outputs are missing. Run `python scripts/generate_phase6_excel_report.py` "
        "or `python scripts/run_full_demo_pipeline.py` to regenerate the demo outputs."
    )
    st.dataframe(missing[["name", "path"]], width="stretch", hide_index=True)


def _sort_exceptions(exceptions: pd.DataFrame) -> pd.DataFrame:
    if exceptions.empty or "severity" not in exceptions.columns:
        return exceptions
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_frame = exceptions.copy()
    sorted_frame["_severity_order"] = sorted_frame["severity"].map(severity_order).fillna(9)
    return sorted_frame.sort_values(["_severity_order", "timestamp"]).drop(
        columns="_severity_order"
    )


data = _load_data()
missing = missing_required_files(data)

render_sidebar_brand()
selected_page = st.sidebar.radio(
    "Navigation", list(NAV_ITEMS.values()), label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.caption("Regenerate outputs with `python scripts/run_full_demo_pipeline.py`.")

default_date = _service_date(data.daily_summary_base)
scenario, selected_date = _render_topbar("base_actuals", default_date)

summary = get_scenario_daily_summary(data, scenario)
reconciliation = get_scenario_reconciliation(data, scenario)
settlement = get_scenario_settlement(data, scenario)
actuals = get_scenario_actuals(data, scenario)
metrics = get_scenario_metrics(data, scenario)
load_profile = prepare_baseline_optimized_load_profile(data)
reconciliation_profile = prepare_reconciliation_profile(data, scenario)
cost_comparison = prepare_cost_comparison(data, scenario)

_render_missing_inputs(missing)

if selected_date != default_date:
    st.info(
        "The current public demo contains one generated sample date. The date control is display-only for this sample dataset."
    )


if selected_page == "Overview":
    _render_kpi_strip(summary)
    st.write("")
    top_left, top_middle, top_right = st.columns([5, 3, 4])
    with top_left:
        st.markdown('<div class="ev-card">', unsafe_allow_html=True)
        render_panel_header(
            "Baseline vs Optimized Charging Load",
            "Site-cap optimized schedule is the primary public-demo case.",
        )
        site_cap = None
        if not data.optimization_summary_site_cap.empty:
            site_cap = safe_float(
                data.optimization_summary_site_cap.iloc[0].get("site_import_limit_kw")
            )
        st.plotly_chart(
            build_baseline_vs_optimized_chart(load_profile, site_import_limit_kw=site_cap),
            width="stretch",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with top_middle:
        st.markdown('<div class="ev-card">', unsafe_allow_html=True)
        render_panel_header("Scheduled vs Actual Charging", _scenario_summary_text(summary))
        st.plotly_chart(build_scheduled_vs_actual_chart(reconciliation_profile), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with top_right:
        render_panel_header(
            "Market Inputs / Fleet Summary", "Operational inputs for the selected run."
        )
        render_summary_list(_fleet_summary_items(data, metrics))

    st.write("")
    bottom_left, bottom_right = st.columns([6, 6])
    with bottom_left:
        st.markdown('<div class="ev-card">', unsafe_allow_html=True)
        render_panel_header(
            "Settlement Exposure", "Simplified interval-level exposure, not official settlement."
        )
        st.plotly_chart(build_settlement_exposure_chart(settlement), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with bottom_right:
        exceptions = _sort_exceptions(data.exceptions)
        material_count = safe_int(summary.get("material_deviation_intervals"))
        upper, lower = st.container(), st.container()
        with upper:
            st.markdown('<div class="ev-card">', unsafe_allow_html=True)
            render_panel_header("Exceptions", "Analyst review queue.")
            if material_count == 0 and scenario == "base_actuals":
                render_empty_exceptions_state()
            else:
                severity_summary = prepare_exception_summary(exceptions, "severity")
                st.plotly_chart(
                    build_exceptions_by_severity_chart(severity_summary), width="stretch"
                )
                visible_cols = [
                    col
                    for col in [
                        "timestamp",
                        "category",
                        "severity",
                        "entity_id",
                        "message",
                        "suggested_action",
                    ]
                    if col in exceptions.columns
                ]
                st.dataframe(exceptions[visible_cols].head(8), width="stretch", hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with lower:
            st.write("")
            st.markdown('<div class="ev-card">', unsafe_allow_html=True)
            render_panel_header("Outputs & Downloads", "Generated reporting artifacts.")
            excel_path = (
                PROJECT_ROOT / "data" / "outputs" / "ev_flex_daily_trading_report_sample.xlsx"
            )
            render_download_card(
                "Daily Trading Report (Excel)",
                "Schedules, prices, exposure, exceptions, and assumptions.",
            )
            if excel_path.exists():
                st.download_button(
                    "Download Excel report",
                    excel_path.read_bytes(),
                    file_name=excel_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )
            st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    render_disclaimer_bar(DISCLAIMER)

elif selected_page == "Fleet & Market Inputs":
    render_panel_header(
        "Fleet & Market Inputs",
        "Synthetic EV fleet requirements and normalized sample market prices.",
    )
    fleet = data.fleet_requirements
    cols = st.columns(5)
    cols[0].metric("Vehicles", format_integer(len(fleet)))
    cols[1].metric(
        "Required energy", format_mwh(fleet["required_kwh"].sum() / 1000 if not fleet.empty else 0)
    )
    cols[2].metric(
        "Avg start SoC", format_pct(fleet["start_soc_pct"].mean() if not fleet.empty else 0)
    )
    cols[3].metric(
        "Avg target SoC", format_pct(fleet["target_soc_pct"].mean() if not fleet.empty else 0)
    )
    cols[4].metric("Readiness target", "100.0%")
    left, right = st.columns([6, 6])
    with left:
        if not data.market_prices.empty:
            fig = px.line(
                data.market_prices.sort_values("settlement_period"),
                x="settlement_period",
                y="price_gbp_per_mwh",
                labels={"settlement_period": "Settlement period", "price_gbp_per_mwh": "GBP/MWh"},
                title="Synthetic/sample market price curve",
            )
            st.plotly_chart(apply_dashboard_layout(fig, height=340), width="stretch")
    with right:
        if not fleet.empty:
            fig = px.bar(
                fleet.sort_values("required_kwh", ascending=False).head(24),
                x="vehicle_id",
                y="required_kwh",
                color="priority" if "priority" in fleet.columns else None,
                labels={"vehicle_id": "Vehicle", "required_kwh": "Required kWh"},
                title="Required kWh by vehicle",
            )
            st.plotly_chart(apply_dashboard_layout(fig, height=340), width="stretch")
    st.dataframe(fleet, width="stretch", hide_index=True)

elif selected_page == "Baseline vs Optimized":
    render_panel_header(
        "Baseline vs Optimized",
        "Immediate charging compared with the site-cap optimized schedule.",
    )
    if not data.optimization_summary_site_cap.empty:
        opt = data.optimization_summary_site_cap.iloc[0]
        cols = st.columns(5)
        cols[0].metric("Baseline cost", format_gbp(opt.get("baseline_cost_gbp")))
        cols[1].metric("Optimized cost", format_gbp(opt.get("optimized_cost_gbp")))
        cols[2].metric(
            "Savings", format_gbp(opt.get("savings_gbp")), format_pct(opt.get("savings_pct"))
        )
        cols[3].metric("Optimized peak", format_kw(opt.get("optimized_peak_import_kw")))
        cols[4].metric("Readiness", format_pct(opt.get("vehicle_readiness_pct")))
    st.plotly_chart(build_baseline_vs_optimized_chart(load_profile, height=440), width="stretch")
    st.plotly_chart(build_cost_comparison_chart(cost_comparison), width="stretch")
    st.dataframe(load_profile, width="stretch", hide_index=True)

elif selected_page == "Scheduled vs Actual":
    render_panel_header(
        "Scheduled vs Actual", "Scenario-aware reconciliation by settlement period."
    )
    st.plotly_chart(
        build_scheduled_vs_actual_chart(reconciliation_profile, height=420), width="stretch"
    )
    if not reconciliation_profile.empty:
        status_counts = (
            reconciliation_profile.groupby("reconciliation_status")
            .size()
            .reset_index(name="interval_count")
        )
        left, right = st.columns([4, 8])
        with left:
            st.dataframe(status_counts, width="stretch", hide_index=True)
        with right:
            review = reconciliation_profile[
                reconciliation_profile["reconciliation_status"].isin(
                    ["material_deviation", "missing_actual"]
                )
            ]
            if review.empty:
                st.success("No intervals require manual review for the selected scenario.")
            else:
                st.dataframe(review, width="stretch", hide_index=True)
    st.dataframe(reconciliation, width="stretch", hide_index=True)

elif selected_page == "Settlement Exposure":
    render_panel_header(
        "Settlement Exposure",
        "Simplified settlement-style exposure. This is not official BSC settlement.",
    )
    if not settlement.empty:
        cols = st.columns(4)
        cols[0].metric("Scheduled cost", format_gbp(settlement["scheduled_cost_gbp"].sum()))
        cols[1].metric(
            "Deviation priced at imbalance",
            format_gbp(settlement["imbalance_exposure_gbp"].sum()),
        )
        cols[2].metric(
            "Settlement-style cost",
            format_gbp(settlement["total_settlement_style_cost_gbp"].sum()),
        )
        cols[3].metric(
            "Avg scheduled price",
            format_gbp_per_mwh(settlement["scheduled_price_gbp_per_mwh"].mean()),
        )
    left, right = st.columns([8, 4])
    with left:
        st.plotly_chart(build_settlement_exposure_chart(settlement, height=420), width="stretch")
    with right:
        render_summary_list(
            [
                ("Scheduled energy", format_mwh(summary.get("scheduled_mwh"))),
                (
                    "Settlement-style cost",
                    format_gbp(summary.get("total_settlement_style_cost_gbp")),
                ),
                ("Dumb baseline cost", format_gbp(summary.get("dumb_baseline_cost_gbp"))),
                ("Optimized expected cost", format_gbp(summary.get("optimized_expected_cost_gbp"))),
                ("Realized savings", format_gbp(summary.get("realized_savings_vs_baseline_gbp"))),
                (
                    "Savings vs baseline",
                    format_pct(summary.get("realized_savings_vs_baseline_pct")),
                ),
            ]
        )
    st.caption(
        "Settlement-style exposure is simplified and illustrative. It is not official BSC settlement."
    )
    st.dataframe(settlement, width="stretch", hide_index=True)

elif selected_page == "Exceptions":
    render_panel_header("Exceptions", "Structured analyst-review queue.")
    exceptions = _sort_exceptions(data.exceptions)
    if exceptions.empty:
        render_empty_exceptions_state()
    else:
        severity_summary = prepare_exception_summary(exceptions, "severity")
        category_summary = prepare_exception_summary(exceptions, "category")
        left, right = st.columns(2)
        left.plotly_chart(build_exceptions_by_severity_chart(severity_summary), width="stretch")
        fig = px.bar(category_summary, x="category", y="count", title="Exceptions by category")
        right.plotly_chart(apply_dashboard_layout(fig, height=260), width="stretch")
        severities = sorted(exceptions["severity"].dropna().unique().tolist())
        selected = st.multiselect("Severity filter", severities, default=severities)
        filtered = exceptions[exceptions["severity"].isin(selected)] if selected else exceptions
        st.dataframe(filtered, width="stretch", hide_index=True)

elif selected_page == "Data Tables / Downloads":
    render_panel_header("Data Tables / Downloads", "Generated outputs for review and export.")
    excel_path = PROJECT_ROOT / "data" / "outputs" / "ev_flex_daily_trading_report_sample.xlsx"
    col1, col2 = st.columns(2)
    with col1:
        render_download_card(
            "Daily Trading Report (Excel)",
            "Includes schedules, prices, exposure, cost summary, exceptions, and assumptions.",
        )
        if excel_path.exists():
            st.download_button(
                "Download Excel report",
                excel_path.read_bytes(),
                file_name=excel_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
    with col2:
        render_download_card(
            "Sample Data Outputs (CSV)",
            "Daily summary and exception logs for the selected scenario.",
        )
        csv_cols = st.columns(2)
        if not summary.empty:
            csv_cols[0].download_button(
                "Daily summary CSV",
                summary.to_frame().T.to_csv(index=False).encode("utf-8"),
                file_name=f"daily_summary_{scenario}.csv",
                mime="text/csv",
                width="stretch",
            )
        if not data.exceptions.empty:
            csv_cols[1].download_button(
                "Exceptions CSV",
                data.exceptions.to_csv(index=False).encode("utf-8"),
                file_name="phase5_reconciliation_exceptions_sample.csv",
                mime="text/csv",
                width="stretch",
            )
    table_options = {
        "Daily summary": summary.to_frame().T if not summary.empty else pd.DataFrame(),
        "Market participation metrics": (
            metrics.to_frame().T if not metrics.empty else pd.DataFrame()
        ),
        "Baseline schedule": data.baseline_schedule,
        "Optimized schedule": data.optimized_schedule,
        "Actual charging": actuals,
        "Reconciliation": reconciliation,
        "Settlement-style exposure": settlement,
        "Exceptions": data.exceptions,
    }
    selected_table = st.selectbox("Preview table", list(table_options))
    st.dataframe(table_options[selected_table], width="stretch", hide_index=True)

else:
    render_panel_header(
        "Methodology & Limitations", "Public-safe methodology and model boundaries."
    )
    st.markdown("""
**Methodology**

- Synthetic EV fleet schedules define vehicle arrival, departure, battery, SoC, and charger constraints.
- Synthetic/sample market prices are normalized to GB half-hourly settlement periods.
- The dumb baseline charges immediately on arrival.
- The smart schedule uses linear optimization with a site import cap as the primary public-demo case.
- Synthetic actual meter scenarios test scheduled-vs-actual reconciliation.
- Settlement-style exposure uses a simplified imbalance-price spread for analytics demonstration.

**Limitations**

- This is not a production trading, dispatch, or official settlement system.
- It uses sample/synthetic data, not live operational data.
- The scheduled position is a simplified proxy for traded energy.
- Imbalance pricing is illustrative unless a public system price series is supplied.
- Charger and site constraints are simplified for a local portfolio demo.
- There is no live market execution, user authentication, cloud deployment, or database backend.
""")
    render_disclaimer_bar(DISCLAIMER)
