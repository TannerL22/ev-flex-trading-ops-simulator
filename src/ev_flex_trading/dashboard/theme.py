"""Dashboard theme tokens and CSS."""

from __future__ import annotations

COLORS = {
    "page": "#F6F8FB",
    "surface": "#FFFFFF",
    "surface_muted": "#F8FAFC",
    "sidebar_top": "#06284D",
    "sidebar_bottom": "#031A36",
    "primary": "#0F172A",
    "secondary": "#475569",
    "muted": "#64748B",
    "blue": "#1769E0",
    "blue_dark": "#0B3B78",
    "blue_soft": "#E8F1FF",
    "teal": "#0EA5A4",
    "green": "#22A447",
    "amber": "#E49A00",
    "purple": "#6D4FD3",
    "orange": "#D97706",
    "gray": "#94A3B8",
    "border": "#E2E8F0",
    "grid": "#E5E7EB",
    "danger": "#B91C1C",
}

CHART_COLORS = {
    "optimized_load": "#4CAF50",
    "optimized_fill": "rgba(76, 175, 80, 0.18)",
    "baseline_load": "#94A3B8",
    "market_price": "#1769E0",
    "scheduled": "#5CB85C",
    "actual": "#2563EB",
    "deviation": "#AAB4C3",
    "scheduled_price": "#2563EB",
    "imbalance_price": "#F97316",
    "exposure_bar": "#22C7C9",
    "site_cap": "#4CAF50",
}

SEVERITY_COLORS = {
    "critical": {"background": "#FEE2E2", "text": "#991B1B", "border": "#FCA5A5"},
    "high": {"background": "#FFE4E6", "text": "#9F1239", "border": "#FDA4AF"},
    "medium": {"background": "#FEF3C7", "text": "#92400E", "border": "#FCD34D"},
    "low": {"background": "#E0F2FE", "text": "#075985", "border": "#7DD3FC"},
    "none": {"background": "#DCFCE7", "text": "#166534", "border": "#86EFAC"},
}


def dashboard_css() -> str:
    """Return Streamlit-safe CSS for the dashboard shell and reusable cards."""

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {{
  --ev-page: {COLORS["page"]};
  --ev-surface: {COLORS["surface"]};
  --ev-border: {COLORS["border"]};
  --ev-primary: {COLORS["primary"]};
  --ev-secondary: {COLORS["secondary"]};
  --ev-muted: {COLORS["muted"]};
  --ev-blue: {COLORS["blue"]};
}}

html, body, [class*="css"] {{
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}}

[data-testid="stAppViewContainer"] {{
  background: var(--ev-page);
}}

#MainMenu, footer, header {{
  visibility: hidden;
}}

.block-container {{
  padding-top: 1.35rem;
  padding-left: 1.6rem;
  padding-right: 1.6rem;
  max-width: none;
}}

[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {COLORS["sidebar_top"]} 0%, {COLORS["sidebar_bottom"]} 100%);
  box-shadow: 4px 0 18px rgba(15, 23, 42, 0.10);
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {{
  color: #FFFFFF !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label {{
  border-radius: 10px;
  padding: 0.35rem 0.2rem;
  margin: 0.18rem 0;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
  background: rgba(255, 255, 255, 0.08);
}}

[data-testid="stSidebar"] hr {{
  border-color: rgba(255, 255, 255, 0.16);
}}

.ev-logo {{
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 10px 2px 18px 2px;
}}

.ev-logo-mark {{
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: #FFFFFF;
  font-weight: 700;
}}

.ev-logo-title {{
  color: #FFFFFF;
  font-weight: 700;
  line-height: 1.15;
}}

.ev-logo-subtitle {{
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  line-height: 1.2;
}}

.ev-topbar {{
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
  padding: 16px 18px;
  margin-bottom: 14px;
}}

.ev-page-title {{
  font-size: 28px;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: 0;
  line-height: 1.15;
  margin: 0;
}}

.ev-page-subtitle {{
  color: #64748B;
  font-size: 13px;
  margin-top: 4px;
}}

.ev-badge {{
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border-radius: 999px;
  background: #E8F1FF;
  color: #0B3B78;
  border: 1px solid #CFE0FF;
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}}

.ev-card {{
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
  padding: 18px;
}}

.ev-kpi-card {{
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

.ev-kpi-top {{
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}}

.ev-kpi-icon {{
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 700;
  flex: 0 0 auto;
}}

.ev-kpi-title {{
  color: #0F172A;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.25;
}}

.ev-kpi-value {{
  color: #0F172A;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.08;
  margin-top: 14px;
  word-break: break-word;
}}

.ev-kpi-subtext {{
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  margin-top: 7px;
}}

.ev-panel-title {{
  font-size: 17px;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 4px 0;
}}

.ev-panel-caption {{
  color: #64748B;
  font-size: 12px;
  margin-bottom: 10px;
}}

.ev-summary-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #EEF2F7;
  padding: 8px 0;
  gap: 12px;
}}

.ev-summary-row:last-child {{
  border-bottom: 0;
}}

.ev-summary-label {{
  color: #475569;
  font-size: 13px;
}}

.ev-summary-value {{
  color: #0F172A;
  font-size: 13px;
  font-weight: 700;
  text-align: right;
}}

.ev-disclaimer {{
  background: #EAF4FF;
  color: #0B3B78;
  border: 1px solid #CFE0FF;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 600;
}}

.ev-download-card {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 14px;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  background: #FFFFFF;
  margin-bottom: 10px;
}}

.ev-download-title {{
  color: #0F172A;
  font-size: 13px;
  font-weight: 700;
}}

.ev-download-desc {{
  color: #64748B;
  font-size: 12px;
  margin-top: 2px;
}}

.ev-empty-state {{
  border: 1px solid #86EFAC;
  background: #DCFCE7;
  color: #166534;
  border-radius: 14px;
  padding: 14px;
}}

.ev-empty-state-title {{
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 4px;
}}

.ev-empty-state-body {{
  font-size: 12px;
  line-height: 1.45;
}}

[data-testid="stDataFrame"] {{
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  overflow: hidden;
}}

h1, h2, h3 {{
  color: #0F172A !important;
  letter-spacing: 0 !important;
}}
</style>
"""
