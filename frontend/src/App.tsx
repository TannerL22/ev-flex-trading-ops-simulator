import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Info,
  Zap
} from "lucide-react";
import {
  BaselineOptimizedChart,
  CostComparisonChart,
  ExceptionsSeverityChart,
  MarketPriceChart,
  ScheduledActualChart,
  SettlementExposureChart
} from "./charts";
import {
  CostSummary,
  DataTable,
  DisclaimerBar,
  DownloadPanel,
  ExceptionsPanel,
  FleetSummaryPanel,
  KpiGrid,
  MissingData,
  Panel,
  Sidebar,
  TopBar
} from "./components";
import {
  displayScenario,
  formatGbp,
  formatInteger,
  formatKw,
  formatMwh,
  formatPct,
  metricFrom,
  numeric,
  text
} from "./format";
import type { DashboardPayload, DataRecord, NavItem, ScenarioKey } from "./types";

const dataUrl = "/data/dashboard.json";

function first(records: DataRecord[]): DataRecord {
  return records.length > 0 ? records[0] : {};
}

function reportDate(payload: DashboardPayload | null): string {
  const row = payload?.scenarios.base_actuals.dailySummary;
  const value = row?.service_date || first(payload?.fleetRequirements || []).service_date;
  return text(value, "Sample date");
}

function statusCounts(reconciliation: DataRecord[]) {
  return reconciliation.reduce<Record<string, number>>((acc, row) => {
    const status = text(row.reconciliation_status, "unknown");
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});
}

function filterExceptions(exceptions: DataRecord[], scenario: ScenarioKey) {
  return exceptions.filter((row) => !row.actuals_scenario || row.actuals_scenario === scenario);
}

export default function App() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState<string | undefined>();
  const [active, setActive] = useState<NavItem["id"]>("overview");
  const [scenario, setScenario] = useState<ScenarioKey>("base_actuals");

  useEffect(() => {
    fetch(dataUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Could not load ${dataUrl} (${response.status})`);
        }
        return response.json();
      })
      .then((data: DashboardPayload) => {
        setPayload(data);
        setScenario(data.metadata.defaultScenario || "base_actuals");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const scenarioData = payload?.scenarios[scenario];
  const summary = scenarioData?.dailySummary || {};
  const metrics = scenarioData?.marketMetrics || {};
  const optimization = first(payload?.optimizationSummarySiteCap || []);
  const reconciliation = scenarioData?.reconciliation || [];
  const settlement = scenarioData?.settlementExposure || [];
  const exceptions = filterExceptions(payload?.exceptions || [], scenario);
  const exceptionSeverity = useMemo(() => {
    const counts = exceptions.reduce<Record<string, number>>((acc, row) => {
      const severity = text(row.severity, "low").toLowerCase();
      acc[severity] = (acc[severity] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts).map(([severity, count]) => ({ severity, count }));
  }, [exceptions]);

  if (error || !payload) {
    return <MissingData error={error} />;
  }

  return (
    <div className="app-shell">
      <Sidebar active={active} onChange={setActive} />
      <div className="main-shell">
        <TopBar scenario={scenario} onScenarioChange={setScenario} reportDate={reportDate(payload)} />
        <main className="content">
          {active === "overview" ? (
            <Overview
              payload={payload}
              scenario={scenario}
              summary={summary}
              metrics={metrics}
              optimization={optimization}
              reconciliation={reconciliation}
              settlement={settlement}
            />
          ) : null}
          {active === "fleet_market" ? <FleetMarket payload={payload} summary={summary} metrics={metrics} optimization={optimization} /> : null}
          {active === "baseline_optimized" ? <BaselineOptimized payload={payload} scenarioData={scenarioData} summary={summary} /> : null}
          {active === "scheduled_actual" ? <ScheduledActual scenario={scenario} reconciliation={reconciliation} /> : null}
          {active === "settlement_exposure" ? <SettlementExposure settlement={settlement} summary={summary} /> : null}
          {active === "exceptions" ? <ExceptionsView exceptions={exceptions} exceptionSeverity={exceptionSeverity} /> : null}
          {active === "downloads" ? <Downloads payload={payload} scenario={scenario} /> : null}
          {active === "methodology" ? <Methodology disclaimer={payload.metadata.disclaimer} /> : null}
        </main>
      </div>
    </div>
  );
}

function Overview({
  payload,
  scenario,
  summary,
  metrics,
  optimization,
  reconciliation,
  settlement
}: {
  payload: DashboardPayload;
  scenario: ScenarioKey;
  summary: DataRecord;
  metrics: DataRecord;
  optimization: DataRecord;
  reconciliation: DataRecord[];
  settlement: DataRecord[];
}) {
  return (
    <>
      <KpiGrid summary={summary} />
      <div className="overview-grid top">
        <Panel
          title="Baseline vs Optimized Charging Load"
          subtitle="Site import power with market price overlay"
          className="span-5"
        >
          <BaselineOptimizedChart data={payload.baselineOptimizedLoad} />
        </Panel>
        <Panel
          title="Scheduled vs Actual Charging"
          subtitle={scenario === "base_actuals" ? "Base case tracks closely" : "High-deviation stress case"}
          className="span-3"
        >
          <ScheduledActualChart data={reconciliation} />
          <div className={`status-strip ${scenario === "base_actuals" ? "healthy" : "warning"}`}>
            {scenario === "base_actuals"
              ? "Tracking performance is close to schedule."
              : "Material deviations and missing meter intervals detected."}
          </div>
        </Panel>
        <Panel title="Market Inputs / Fleet Summary" className="span-4">
          <FleetSummaryPanel
            fleet={payload.fleetRequirements}
            summary={summary}
            metrics={metrics}
            optimization={optimization}
          />
        </Panel>
      </div>
      <div className="overview-grid bottom">
        <Panel title="Settlement Exposure" subtitle="Simplified interval-level exposure" className="span-6">
          <div className="split-panel">
            <div className="chart-side">
              <SettlementExposureChart data={settlement} />
            </div>
            <CostSummary summary={summary} />
          </div>
        </Panel>
        <div className="stacked span-6">
          <Panel title="Exceptions" subtitle="Analyst review queue">
            <ExceptionsPanel exceptions={payload.exceptions} scenario={scenario} />
          </Panel>
          <Panel title="Outputs & Downloads">
            <DownloadPanel excelUrl={payload.metadata.excelReportUrl} />
          </Panel>
        </div>
      </div>
      <DisclaimerBar text={payload.metadata.disclaimer} />
    </>
  );
}

function FleetMarket({
  payload,
  summary,
  metrics,
  optimization
}: {
  payload: DashboardPayload;
  summary: DataRecord;
  metrics: DataRecord;
  optimization: DataRecord;
}) {
  return (
    <div className="page-stack">
      <div className="three-grid">
        <Panel title="Fleet Summary">
          <FleetSummaryPanel
            fleet={payload.fleetRequirements}
            summary={summary}
            metrics={metrics}
            optimization={optimization}
          />
        </Panel>
        <Panel title="Market Price Curve" className="wide-2">
          <ResponsivePriceChart data={payload.marketPrices} />
        </Panel>
      </div>
      <Panel title="Fleet Requirements Preview" subtitle="Synthetic EV fleet schedule and charging requirements">
        <DataTable rows={payload.fleetRequirements} />
      </Panel>
      <Panel title="Market Prices Preview" subtitle="Synthetic/sample half-hourly price data">
        <DataTable rows={payload.marketPrices} />
      </Panel>
    </div>
  );
}

function ResponsivePriceChart({ data }: { data: DataRecord[] }) {
  return <MarketPriceChart data={data} />;
}

function BaselineOptimized({
  payload,
  scenarioData,
  summary
}: {
  payload: DashboardPayload;
  scenarioData?: { costComparison: DataRecord[] };
  summary: DataRecord;
}) {
  return (
    <div className="page-stack">
      <Panel title="Baseline vs Optimized Charging Load" subtitle="Immediate charging compared with site-cap price optimization">
        <BaselineOptimizedChart data={payload.baselineOptimizedLoad} />
      </Panel>
      <div className="two-grid">
        <Panel title="Cost Comparison">
          <CostComparisonChart data={scenarioData?.costComparison || []} />
        </Panel>
        <Panel title="Comparison Metrics">
          <div className="summary-list">
            <MetricRow label="Dumb baseline cost" value={formatGbp(summary.dumb_baseline_cost_gbp, 2)} />
            <MetricRow label="Optimized expected cost" value={formatGbp(summary.optimized_expected_cost_gbp, 2)} />
            <MetricRow label="Realized savings" value={formatGbp(summary.realized_savings_vs_baseline_gbp, 2)} />
            <MetricRow label="Savings vs baseline" value={formatPct(summary.realized_savings_vs_baseline_pct)} />
            <MetricRow label="Vehicle readiness" value={formatPct(summary.vehicle_readiness_pct, 0)} />
          </div>
        </Panel>
      </div>
    </div>
  );
}

function ScheduledActual({ scenario, reconciliation }: { scenario: ScenarioKey; reconciliation: DataRecord[] }) {
  const counts = statusCounts(reconciliation);
  return (
    <div className="page-stack">
      <Panel title="Scheduled vs Actual Charging" subtitle={`${displayScenario(scenario)} reconciliation by settlement period`}>
        <ScheduledActualChart data={reconciliation} />
      </Panel>
      <div className="two-grid">
        <Panel title="Reconciliation Status Counts">
          <div className="summary-list">
            {Object.entries(counts).map(([status, count]) => (
              <MetricRow key={status} label={status.replaceAll("_", " ")} value={formatInteger(count)} />
            ))}
          </div>
        </Panel>
        <Panel title="Material Intervals Preview">
          <DataTable
            rows={reconciliation.filter((row) =>
              ["material_deviation", "missing_actual", "missing_schedule"].includes(
                text(row.reconciliation_status)
              )
            )}
          />
        </Panel>
      </div>
      <Panel title="Reconciliation Table">
        <DataTable rows={reconciliation} maxRows={18} />
      </Panel>
    </div>
  );
}

function SettlementExposure({ settlement, summary }: { settlement: DataRecord[]; summary: DataRecord }) {
  return (
    <div className="page-stack">
      <Panel title="Settlement-style Exposure" subtitle="Simplified deviation pricing, not official settlement">
        <div className="split-panel">
          <div className="chart-side">
            <SettlementExposureChart data={settlement} />
          </div>
          <CostSummary summary={summary} />
        </div>
      </Panel>
      <Panel title="Interval-level Exposure Table">
        <DataTable rows={settlement} maxRows={18} />
      </Panel>
    </div>
  );
}

function ExceptionsView({
  exceptions,
  exceptionSeverity
}: {
  exceptions: DataRecord[];
  exceptionSeverity: DataRecord[];
}) {
  return (
    <div className="page-stack">
      <div className="two-grid">
        <Panel title="Exceptions by Severity">
          {exceptionSeverity.length > 0 ? (
            <ExceptionsSeverityChart data={exceptionSeverity} />
          ) : (
            <div className="empty-state healthy">
              <CheckCircle2 size={32} />
              <h3>No exceptions for the selected scenario.</h3>
            </div>
          )}
        </Panel>
        <Panel title="Review Queue">
          <ExceptionsPanel exceptions={exceptions} scenario="high_deviation" />
        </Panel>
      </div>
      <Panel title="Exception Detail">
        <DataTable rows={exceptions} maxRows={24} />
      </Panel>
    </div>
  );
}

function Downloads({ payload, scenario }: { payload: DashboardPayload; scenario: ScenarioKey }) {
  const scenarioData = payload.scenarios[scenario];
  return (
    <div className="page-stack">
      <Panel title="Outputs & Downloads" subtitle="Generated demo artifacts">
        <DownloadPanel excelUrl={payload.metadata.excelReportUrl} />
      </Panel>
      <div className="two-grid">
        <Panel title="Daily Summary">
          <DataTable rows={[scenarioData.dailySummary]} />
        </Panel>
        <Panel title="Market Participation Metrics">
          <DataTable rows={[scenarioData.marketMetrics]} />
        </Panel>
      </div>
      <Panel title="Processed Dataset Preview">
        <DataTable rows={scenarioData.reconciliation} maxRows={18} />
      </Panel>
    </div>
  );
}

function Methodology({ disclaimer }: { disclaimer: string }) {
  return (
    <div className="page-stack methodology">
      <Panel title="Methodology">
        <div className="method-grid">
          <MethodCard
            icon={<Database />}
            title="Synthetic and sample inputs"
            body="The demo uses synthetic EV fleet schedules and synthetic/sample market price data so the project can be shared publicly."
          />
          <MethodCard
            icon={<Zap />}
            title="Immediate baseline"
            body="The dumb baseline charges vehicles immediately on arrival, subject to vehicle charger limits and plug-in windows."
          />
          <MethodCard
            icon={<BarChart3 />}
            title="Smart charging optimization"
            body="A linear optimization model shifts charging into lower-price settlement periods while maintaining readiness and a 750 kW site import cap."
          />
          <MethodCard
            icon={<AlertTriangle />}
            title="Reconciliation and exposure"
            body="Synthetic actuals are reconciled to the scheduled position and priced with a simplified settlement-style exposure model."
          />
        </div>
      </Panel>
      <Panel title="Limitations">
        <ul className="limitations-list">
          <li>{disclaimer}</li>
          <li>Actual charging is synthetic; no live operational data is used.</li>
          <li>Settlement-style exposure is simplified and not official BSC settlement.</li>
          <li>The P&L-style summary is illustrative and not real trading P&L.</li>
          <li>There is no trade execution, dispatch control, authentication, or cloud backend.</li>
        </ul>
      </Panel>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MethodCard({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <article className="method-card">
      <div className="summary-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}
