"""Reusable Streamlit dashboard components."""

from __future__ import annotations

from html import escape

import streamlit as st

from ev_flex_trading.dashboard.theme import COLORS


def render_sidebar_brand() -> None:
    """Render the product mark in the Streamlit sidebar."""

    st.sidebar.markdown(
        """
<div class="ev-logo">
  <div class="ev-logo-mark">EV</div>
  <div>
    <div class="ev-logo-title">EV Flex Trading</div>
    <div class="ev-logo-subtitle">Ops Simulator</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def kpi_card_html(
    *,
    title: str,
    value: str,
    subtext: str = "",
    icon: str = "",
    accent_color: str = COLORS["blue"],
) -> str:
    """Build KPI card HTML for testing and rendering."""

    safe_title = escape(title)
    safe_value = escape(value)
    safe_subtext = escape(subtext)
    safe_icon = escape(icon or title[:2].upper())
    return f"""
<div class="ev-card ev-kpi-card">
  <div class="ev-kpi-top">
    <div class="ev-kpi-title">{safe_title}</div>
    <div class="ev-kpi-icon" style="background:{accent_color}1A;color:{accent_color};">{safe_icon}</div>
  </div>
  <div>
    <div class="ev-kpi-value">{safe_value}</div>
    <div class="ev-kpi-subtext">{safe_subtext}</div>
  </div>
</div>
"""


def render_kpi_card(
    *,
    title: str,
    value: str,
    subtext: str = "",
    icon: str = "",
    accent_color: str = COLORS["blue"],
) -> None:
    """Render a KPI card."""

    st.markdown(
        kpi_card_html(
            title=title,
            value=value,
            subtext=subtext,
            icon=icon,
            accent_color=accent_color,
        ),
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, caption: str = "") -> None:
    """Render a card/panel heading."""

    st.markdown(
        f"""
<div>
  <div class="ev-panel-title">{escape(title)}</div>
  <div class="ev-panel-caption">{escape(caption)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_info_badge(label: str) -> None:
    """Render a pill-shaped info badge."""

    st.markdown(f'<span class="ev-badge">{escape(label)}</span>', unsafe_allow_html=True)


def render_disclaimer_bar(text: str) -> None:
    """Render the public-demo disclaimer bar."""

    st.markdown(f'<div class="ev-disclaimer">{escape(text)}</div>', unsafe_allow_html=True)


def render_download_card(title: str, description: str) -> None:
    """Render a visual download-card label above Streamlit download buttons."""

    st.markdown(
        f"""
<div class="ev-download-card">
  <div>
    <div class="ev-download-title">{escape(title)}</div>
    <div class="ev-download-desc">{escape(description)}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_empty_exceptions_state() -> None:
    """Render the healthy base-case exception state."""

    st.markdown(
        """
<div class="ev-empty-state">
  <div class="ev-empty-state-title">No material deviations in the base case.</div>
  <div class="ev-empty-state-body">
    All scheduled vs actual volumes are within tolerance. The system will surface and
    prioritize high deviations here.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def summary_list_html(items: list[tuple[str, str]]) -> str:
    """Build a compact label-value summary list."""

    rows = "\n".join(f"""
<div class="ev-summary-row">
  <div class="ev-summary-label">{escape(label)}</div>
  <div class="ev-summary-value">{escape(value)}</div>
</div>
""" for label, value in items)
    return f'<div class="ev-card">{rows}</div>'


def render_summary_list(items: list[tuple[str, str]]) -> None:
    """Render a compact label-value summary list."""

    st.markdown(summary_list_html(items), unsafe_allow_html=True)
