import type { DataRecord } from "./types";

export function numeric(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

export function text(value: unknown, fallback = "n/a"): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

export function formatMwh(value: unknown, digits = 3): string {
  return `${numeric(value).toFixed(digits)} MWh`;
}

export function formatKwh(value: unknown, digits = 1): string {
  return `${numeric(value).toFixed(digits)} kWh`;
}

export function formatKw(value: unknown, digits = 0): string {
  return `${numeric(value).toLocaleString("en-GB", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  })} kW`;
}

export function formatGbp(value: unknown, digits = 0): string {
  return numeric(value).toLocaleString("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  });
}

export function formatGbpPerMwh(value: unknown): string {
  return `${formatGbp(value, 2)} /MWh`;
}

export function formatPct(value: unknown, digits = 1): string {
  const raw = numeric(value);
  const pct = Math.abs(raw) <= 1 ? raw * 100 : raw;
  return `${pct.toFixed(digits)}%`;
}

export function formatInteger(value: unknown): string {
  return Math.round(numeric(value)).toLocaleString("en-GB");
}

export function metricFrom(record: DataRecord, key: string, fallback = 0): number {
  return numeric(record[key], fallback);
}

export function displayScenario(scenario: string): string {
  return scenario === "high_deviation" ? "High deviation" : "Base actuals";
}

export function periodLabel(value: unknown): string {
  const period = Math.round(numeric(value));
  return period > 0 ? `SP ${period}` : "";
}
