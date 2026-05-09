# UI Implementation Notes

The polished dashboard is implemented as a React/Vite frontend in `frontend/`. It reads a static JSON payload exported by `scripts/export_dashboard_json.py`, which keeps the Python analytics pipeline unchanged while giving the presentation layer full control over layout, styling, and interaction.

The Streamlit dashboard remains in `app/streamlit_app.py` as a fallback and data-review interface. The React dashboard is the preferred public demo surface.

## Design Approach

- Fixed left navigation rail with deep navy styling.
- Top control bar with scenario selector, report date, and synthetic/sample data badge.
- Eight-card KPI strip before detailed charts.
- Site-cap optimized load is the hero case.
- Recharts powers the dashboard charts.
- `lucide-react` provides consistent iconography.
- Public-safe disclaimer remains visible on the overview.

## Intentional Constraints

- The frontend is a local static app, not a cloud deployment.
- Downloads are served from files copied into `frontend/public/` by the export script.
- The app does not execute analytics in the browser; it presents the generated Python outputs.
- No live trading, dispatch, operational data, or official settlement functionality is included.
