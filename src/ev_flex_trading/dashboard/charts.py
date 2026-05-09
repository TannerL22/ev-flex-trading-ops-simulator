"""Plotly chart builders for the dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ev_flex_trading.dashboard.theme import CHART_COLORS, COLORS


def apply_dashboard_layout(fig: go.Figure, *, height: int | None = None) -> go.Figure:
    """Apply shared Plotly styling."""

    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
        hovermode="x unified",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        legend_title=None,
        margin={"l": 46, "r": 46, "t": 48, "b": 46},
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["grid"], tickfont={"color": COLORS["muted"]})
    fig.update_yaxes(gridcolor=COLORS["grid"], tickfont={"color": COLORS["muted"]})
    if height is not None:
        fig.update_layout(height=height)
    return fig


def build_baseline_vs_optimized_chart(
    profile: pd.DataFrame,
    *,
    site_import_limit_kw: float | None = 750.0,
    height: int = 360,
) -> go.Figure:
    """Build the hero baseline-vs-optimized charging chart."""

    fig = go.Figure()
    if profile.empty:
        return apply_dashboard_layout(fig, height=height)

    fig.add_trace(
        go.Scatter(
            x=profile["settlement_period"],
            y=profile["optimized_kw"],
            mode="lines",
            name="Optimized (site cap)",
            line={"color": CHART_COLORS["optimized_load"], "width": 3, "shape": "hv"},
            fill="tozeroy",
            fillcolor=CHART_COLORS["optimized_fill"],
            hovertemplate="SP %{x}<br>Optimized %{y:.1f} kW<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=profile["settlement_period"],
            y=profile["baseline_kw"],
            mode="lines",
            name="Dumb baseline",
            line={
                "color": CHART_COLORS["baseline_load"],
                "width": 2,
                "dash": "dash",
                "shape": "hv",
            },
            hovertemplate="SP %{x}<br>Baseline %{y:.1f} kW<extra></extra>",
        )
    )
    if "price_gbp_per_mwh" in profile.columns:
        fig.add_trace(
            go.Scatter(
                x=profile["settlement_period"],
                y=profile["price_gbp_per_mwh"],
                mode="lines",
                name="Market price",
                yaxis="y2",
                line={"color": CHART_COLORS["market_price"], "width": 2},
                hovertemplate="SP %{x}<br>Price £%{y:.2f}/MWh<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2={
                "title": "Price (£/MWh)",
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
                "tickfont": {"color": COLORS["muted"]},
            }
        )
    if site_import_limit_kw:
        fig.add_hline(
            y=site_import_limit_kw,
            line_dash="dash",
            line_color=CHART_COLORS["site_cap"],
            annotation_text=f"Site cap {site_import_limit_kw:.0f} kW",
            annotation_position="top left",
        )
    fig.update_layout(xaxis_title="Settlement period", yaxis_title="Power (kW)")
    return apply_dashboard_layout(fig, height=height)


def build_scheduled_vs_actual_chart(profile: pd.DataFrame, *, height: int = 300) -> go.Figure:
    """Build scheduled-vs-actual and deviation chart."""

    fig = go.Figure()
    if profile.empty:
        return apply_dashboard_layout(fig, height=height)
    fig.add_bar(
        x=profile["settlement_period"],
        y=profile["deviation_mwh"],
        name="Deviation MWh",
        marker_color=CHART_COLORS["deviation"],
        opacity=0.55,
        hovertemplate="SP %{x}<br>Deviation %{y:.4f} MWh<extra></extra>",
    )
    fig.add_trace(
        go.Scatter(
            x=profile["settlement_period"],
            y=profile["scheduled_mwh"],
            mode="lines+markers",
            name="Scheduled MWh",
            line={"color": CHART_COLORS["scheduled"], "width": 2.5},
            hovertemplate="SP %{x}<br>Scheduled %{y:.4f} MWh<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=profile["settlement_period"],
            y=profile["actual_mwh"],
            mode="lines+markers",
            name="Actual MWh",
            line={"color": CHART_COLORS["actual"], "width": 2.5},
            hovertemplate="SP %{x}<br>Actual %{y:.4f} MWh<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Settlement period", yaxis_title="Energy (MWh)")
    return apply_dashboard_layout(fig, height=height)


def build_settlement_exposure_chart(settlement: pd.DataFrame, *, height: int = 320) -> go.Figure:
    """Build price and settlement-style exposure chart."""

    fig = go.Figure()
    if settlement.empty:
        return apply_dashboard_layout(fig, height=height)
    ordered = settlement.sort_values("settlement_period")
    fig.add_bar(
        x=ordered["settlement_period"],
        y=ordered["imbalance_exposure_gbp"],
        name="Exposure (£)",
        marker_color=CHART_COLORS["exposure_bar"],
        opacity=0.72,
        yaxis="y2",
    )
    fig.add_trace(
        go.Scatter(
            x=ordered["settlement_period"],
            y=ordered["scheduled_price_gbp_per_mwh"],
            mode="lines",
            name="Scheduled price",
            line={"color": CHART_COLORS["scheduled_price"], "width": 2.5},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ordered["settlement_period"],
            y=ordered["imbalance_price_gbp_per_mwh"],
            mode="lines",
            name="Imbalance price",
            line={"color": CHART_COLORS["imbalance_price"], "width": 2.5},
        )
    )
    fig.update_layout(
        xaxis_title="Settlement period",
        yaxis_title="Price (£/MWh)",
        yaxis2={
            "title": "Exposure (£)",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "tickfont": {"color": COLORS["muted"]},
        },
    )
    return apply_dashboard_layout(fig, height=height)


def build_cost_comparison_chart(costs: pd.DataFrame, *, height: int = 300) -> go.Figure:
    """Build cost comparison bar chart."""

    if costs.empty:
        return apply_dashboard_layout(go.Figure(), height=height)
    fig = px.bar(
        costs,
        x="cost_type",
        y="cost_gbp",
        color="cost_type",
        color_discrete_sequence=[
            COLORS["gray"],
            COLORS["teal"],
            COLORS["purple"],
        ],
        labels={"cost_type": "", "cost_gbp": "Cost (£)"},
    )
    fig.update_layout(showlegend=False)
    return apply_dashboard_layout(fig, height=height)


def build_exceptions_by_severity_chart(summary: pd.DataFrame, *, height: int = 260) -> go.Figure:
    """Build exception count by severity chart."""

    if summary.empty:
        return apply_dashboard_layout(go.Figure(), height=height)
    severity_order = ["critical", "high", "medium", "low"]
    summary = summary.copy()
    summary["severity"] = pd.Categorical(summary["severity"], severity_order, ordered=True)
    summary = summary.sort_values("severity")
    fig = px.bar(
        summary,
        x="severity",
        y="count",
        color="severity",
        color_discrete_map={
            "critical": "#991B1B",
            "high": "#9F1239",
            "medium": "#E49A00",
            "low": "#1769E0",
        },
        labels={"severity": "Severity", "count": "Count"},
    )
    fig.update_layout(showlegend=False)
    return apply_dashboard_layout(fig, height=height)
