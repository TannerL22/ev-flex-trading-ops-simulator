# EV Flex Trading Dashboard

React/Vite presentation layer for the EV Flex Trading Ops Simulator.

Run from this directory:

```bash
npm install
npm run dev
```

Before running the dashboard, generate the static dataset from the project root:

```bash
python scripts/run_full_demo_pipeline.py
```

The app reads `frontend/public/data/dashboard.json` and serves the copied Excel report from `frontend/public/reports/`.
