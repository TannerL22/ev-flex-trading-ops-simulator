import {
  AlertTriangle,
  BarChart3,
  BatteryCharging,
  BookOpen,
  Bus,
  CheckCircle2,
  CircleHelp,
  Database,
  Download,
  FileSpreadsheet,
  Grid3X3,
  Info,
  LineChart,
  PoundSterling,
  ShieldCheck,
  TrendingUp,
  Zap
} from "lucide-react";
import type { ReactNode } from "react";
import type { DataRecord, NavItem } from "./types";
import { formatGbp, formatInteger, formatKw, formatMwh, formatPct, numeric, text } from "./format";

export const navItems: NavItem[] = [
  { id: "overview", label: "Overview" },
  { id: "fleet_market", label: "Fleet & Market Inputs" },
  { id: "baseline_optimized", label: "Baseline vs Optimized" },
  { id: "scheduled_actual", label: "Scheduled vs Actual" },
  { id: "settlement_exposure", label: "Settlement Exposure" },
  { id: "exceptions", label: "Exceptions" },
  { id: "downloads", label: "Data Tables / Downloads" },
  { id: "methodology", label: "Methodology & Limitations" }
];

const navIcons: Record<NavItem["id"], ReactNode> = {
  overview: <Grid3X3 size={18} />,
  fleet_market: <Bus size={18} />,
  baseline_optimized: <BarChart3 size={18} />,
  scheduled_actual: <LineChart size={18} />,
  settlement_exposure: <PoundSterling size={18} />,
  exceptions: <AlertTriangle size={18} />,
  downloads: <Database size={18} />,
  methodology: <BookOpen size={18} />
};

const severityOrder: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3
};

export function Sidebar({
  active,
  onChange
}: {
  active: NavItem["id"];
  onChange: (id: NavItem["id"]) => void;
}) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Zap size={22} />
        </div>
        <div>
          <div className="brand-title">EV Flex Trading</div>
          <div className="brand-subtitle">Ops Simulator</div>
        </div>
      </div>
      <nav className="nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${active === item.id ? "active" : ""}`}
            type="button"
            onClick={() => onChange(item.id)}
          >
            {navIcons[item.id]}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-note">
        <Info size={15} />
        <span>Synthetic/sample data. Not an official settlement system.</span>
      </div>
    </aside>
  );
}

export function TopBar({
  scenario,
  onScenarioChange,
  reportDate,
  onHelpClick
}: {
  scenario: string;
  onScenarioChange: (scenario: "base_actuals" | "high_deviation") => void;
  reportDate: string;
  onHelpClick: () => void;
}) {
  return (
    <header className="topbar">
      <div>
        <h1>EV Flex Trading Ops Simulator</h1>
        <p>Daily EV flexibility trading-support dashboard</p>
      </div>
      <div className="topbar-controls">
        <label className="control">
          <span>Scenario</span>
          <select
            value={scenario}
            onChange={(event) =>
              onScenarioChange(event.target.value as "base_actuals" | "high_deviation")
            }
          >
            <option value="base_actuals">Base actuals</option>
            <option value="high_deviation">High deviation</option>
          </select>
        </label>
        <div className="date-pill">
          <span>Date</span>
          <strong>{reportDate}</strong>
        </div>
        <div className="data-badge">Synthetic / sample data</div>
        <button
          className="icon-button"
          type="button"
          title="Methodology and limitations"
          onClick={onHelpClick}
        >
          <CircleHelp size={19} />
        </button>
      </div>
    </header>
  );
}

export function Panel({
  title,
  subtitle,
  children,
  className = ""
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}

export function KpiGrid({ summary }: { summary: DataRecord }) {
  const material =
    numeric(summary.material_deviation_intervals) + numeric(summary.missing_meter_intervals);
  const actualPct =
    numeric(summary.scheduled_mwh) > 0
      ? numeric(summary.actual_mwh) / numeric(summary.scheduled_mwh)
      : 0;

  const cards = [
    {
      title: "Scheduled MWh",
      value: formatMwh(summary.scheduled_mwh),
      subtext: "Scheduled position",
      icon: <Zap />,
      accent: "blue"
    },
    {
      title: "Actual MWh",
      value: formatMwh(summary.actual_mwh),
      subtext: `${formatPct(actualPct)} of schedule`,
      icon: <LineChart />,
      accent: "teal"
    },
    {
      title: "Settlement-style Cost",
      value: formatGbp(summary.total_settlement_style_cost_gbp),
      subtext: "Illustrative daily cost",
      icon: <PoundSterling />,
      accent: "purple"
    },
    {
      title: "Dumb Baseline Cost",
      value: formatGbp(summary.dumb_baseline_cost_gbp),
      subtext: "Immediate charging",
      icon: <TrendingUp />,
      accent: "orange"
    },
    {
      title: "Optimized Expected Cost",
      value: formatGbp(summary.optimized_expected_cost_gbp),
      subtext: "Site-cap schedule",
      icon: <ShieldCheck />,
      accent: "teal"
    },
    {
      title: "Realized Savings",
      value: formatGbp(summary.realized_savings_vs_baseline_gbp),
      subtext: `${formatPct(summary.realized_savings_vs_baseline_pct)} vs baseline`,
      icon: <TrendingUp />,
      accent: "green"
    },
    {
      title: "Vehicle Readiness",
      value: formatPct(summary.vehicle_readiness_pct, 0),
      subtext: "On target",
      icon: <Bus />,
      accent: "blue"
    },
    {
      title: "Exceptions",
      value: formatInteger(material),
      subtext: "Material or missing",
      icon: <AlertTriangle />,
      accent: material > 0 ? "amber" : "green"
    }
  ];

  return (
    <div className="kpi-grid">
      {cards.map((card) => (
        <article className="kpi-card" key={card.title}>
          <div className={`kpi-icon ${card.accent}`}>{card.icon}</div>
          <div className="kpi-title">{card.title}</div>
          <div className="kpi-value">{card.value}</div>
          <div className="kpi-subtext">{card.subtext}</div>
        </article>
      ))}
    </div>
  );
}

export function FleetSummaryPanel({
  fleet,
  summary,
  metrics,
  optimization
}: {
  fleet: DataRecord[];
  summary: DataRecord;
  metrics: DataRecord;
  optimization: DataRecord;
}) {
  const totalRequired = fleet.reduce((total, row) => total + numeric(row.required_kwh), 0) / 1000;
  const avgStart =
    fleet.length > 0
      ? fleet.reduce((total, row) => total + numeric(row.start_soc_pct), 0) / fleet.length
      : 0;
  const avgTarget =
    fleet.length > 0
      ? fleet.reduce((total, row) => total + numeric(row.target_soc_pct), 0) / fleet.length
      : 0;
  const rows = [
    ["Number of Vehicles", formatInteger(summary.vehicles_total || fleet.length), <Bus />],
    ["Total Required Energy", formatMwh(totalRequired), <BatteryCharging />],
    ["Average Start SoC", formatPct(avgStart), <LineChart />],
    ["Average Target SoC", formatPct(avgTarget), <ShieldCheck />],
    ["Site Import Cap", formatKw(optimization.site_import_limit_kw || 750), <Zap />],
    ["Active Settlement Periods", formatInteger(metrics.active_settlement_periods), <BarChart3 />],
    ["Market", "Synthetic day-ahead", <Database />]
  ];
  return (
    <div className="summary-list">
      {rows.map(([label, value, icon]) => (
        <div className="summary-row" key={String(label)}>
          <div className="summary-icon">{icon as ReactNode}</div>
          <span>{label}</span>
          <strong>{value as string}</strong>
        </div>
      ))}
    </div>
  );
}

export function CostSummary({ summary }: { summary: DataRecord }) {
  const rows = [
    ["Scheduled energy", formatMwh(summary.scheduled_mwh)],
    ["Settlement-style cost", formatGbp(summary.total_settlement_style_cost_gbp, 2)],
    ["Dumb baseline cost", formatGbp(summary.dumb_baseline_cost_gbp, 2)],
    ["Optimized expected cost", formatGbp(summary.optimized_expected_cost_gbp, 2)],
    ["Realized savings", formatGbp(summary.realized_savings_vs_baseline_gbp, 2)],
    ["Savings vs baseline", formatPct(summary.realized_savings_vs_baseline_pct)]
  ];
  return (
    <div className="cost-summary">
      {rows.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

export function ExceptionsPanel({
  exceptions,
  scenario
}: {
  exceptions: DataRecord[];
  scenario: string;
}) {
  const relevant = exceptions
    .filter((row) => !row.actuals_scenario || row.actuals_scenario === scenario)
    .sort(
      (a, b) =>
        (severityOrder[text(a.severity, "low")] ?? 4) -
        (severityOrder[text(b.severity, "low")] ?? 4)
    );

  if (scenario === "base_actuals" && relevant.length === 0) {
    return (
      <div className="empty-state healthy">
        <CheckCircle2 size={34} />
        <h3>No material deviations in the base case.</h3>
        <p>All scheduled vs actual volumes are within tolerance.</p>
        <p>The system will surface and prioritize high deviations here.</p>
      </div>
    );
  }

  if (relevant.length === 0) {
    return (
      <div className="empty-state healthy">
        <CheckCircle2 size={34} />
        <h3>No exceptions for the selected scenario.</h3>
        <p>Exception handling remains visible for analyst review.</p>
      </div>
    );
  }

  return (
    <div className="exception-list compact">
      {relevant.slice(0, 6).map((row, index) => (
        <div className="exception-item" key={`${text(row.timestamp)}-${index}`}>
          <span className={`severity ${text(row.severity, "low").toLowerCase()}`}>
            {text(row.severity)}
          </span>
          <div>
            <strong>{text(row.category)}</strong>
            <p>{text(row.message)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function DownloadPanel({ excelUrl }: { excelUrl?: string }) {
  const baseUrl = import.meta.env.BASE_URL;
  const dashboardJsonUrl = `${baseUrl}data/dashboard.json`;
  return (
    <div className="download-list">
      <a
        className="download-card"
        href={excelUrl || `${baseUrl}reports/ev_flex_daily_trading_report_sample.xlsx`}
        download
      >
        <div>
          <FileSpreadsheet size={22} />
          <div>
            <strong>Daily Trading Report (Excel)</strong>
            <span>Schedules, prices, exposure and summary</span>
          </div>
        </div>
        <Download size={18} />
      </a>
      <a className="download-card" href={dashboardJsonUrl} download>
        <div>
          <Database size={22} />
          <div>
            <strong>Dashboard Dataset (JSON)</strong>
            <span>Static sample data for this interface</span>
          </div>
        </div>
        <Download size={18} />
      </a>
    </div>
  );
}

export function DisclaimerBar({ text: disclaimer }: { text: string }) {
  return (
    <div className="disclaimer">
      <Info size={18} />
      <span>{disclaimer}</span>
    </div>
  );
}

export function DataTable({ rows, maxRows = 12 }: { rows: DataRecord[]; maxRows?: number }) {
  if (rows.length === 0) {
    return <div className="table-empty">No rows available.</div>;
  }
  const columns = Object.keys(rows[0]).slice(0, 10);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, maxRows).map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{text(row[column], "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function MissingData({ error }: { error?: string }) {
  return (
    <main className="missing-data">
      <AlertTriangle size={40} />
      <h1>Dashboard data is not available</h1>
      <p>
        Required sample outputs are missing. Run{" "}
        <code>python scripts/run_full_demo_pipeline.py</code> from the project root, then restart
        the dashboard.
      </p>
      {error ? <pre>{error}</pre> : null}
    </main>
  );
}
