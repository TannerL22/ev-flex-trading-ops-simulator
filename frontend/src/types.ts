export type ScenarioKey = "base_actuals" | "high_deviation";

export type RecordValue = string | number | boolean | null | undefined;
export type DataRecord = Record<string, RecordValue>;

export interface ScenarioPayload {
  dailySummary: DataRecord;
  marketMetrics: DataRecord;
  reconciliation: DataRecord[];
  settlementExposure: DataRecord[];
  costComparison: DataRecord[];
}

export interface DashboardPayload {
  metadata: {
    projectName: string;
    dataStatus: string;
    disclaimer: string;
    defaultScenario: ScenarioKey;
    excelReportPath: string;
    excelReportUrl?: string;
    generatedFrom: string;
  };
  fleetRequirements: DataRecord[];
  marketPrices: DataRecord[];
  baselineOptimizedLoad: DataRecord[];
  baselineSchedule: DataRecord[];
  optimizedSchedule: DataRecord[];
  actualCharging: Record<ScenarioKey, DataRecord[]>;
  scheduledPosition: DataRecord[];
  exceptions: DataRecord[];
  exceptionsBySeverity: DataRecord[];
  exceptionsByCategory: DataRecord[];
  baselineSummary: DataRecord[];
  optimizationSummarySiteCap: DataRecord[];
  scenarios: Record<ScenarioKey, ScenarioPayload>;
}

export interface NavItem {
  id:
    | "overview"
    | "fleet_market"
    | "baseline_optimized"
    | "scheduled_actual"
    | "settlement_exposure"
    | "exceptions"
    | "downloads"
    | "methodology";
  label: string;
}
