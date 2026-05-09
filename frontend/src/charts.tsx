import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { DataRecord } from "./types";
import { formatGbp, formatGbpPerMwh, formatKw, numeric, periodLabel, text } from "./format";

const axisStyle = {
  fill: "#64748B",
  fontSize: 11
};

const gridColor = "#E5E7EB";

function tooltipLabel(label: unknown) {
  return periodLabel(label);
}

export function BaselineOptimizedChart({ data }: { data: DataRecord[] }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 18, right: 18, bottom: 18, left: 8 }}>
        <CartesianGrid stroke={gridColor} vertical={false} />
        <XAxis
          dataKey="settlement_period"
          tick={axisStyle}
          tickFormatter={(value) => String(Math.round(numeric(value)))}
          label={{ value: "Settlement period", position: "insideBottom", offset: -8 }}
        />
        <YAxis
          yAxisId="left"
          tick={axisStyle}
          width={58}
          tickFormatter={(value) => `${value}`}
          label={{ value: "kW", angle: -90, position: "insideLeft" }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={axisStyle}
          width={60}
          tickFormatter={(value) => `£${value}`}
        />
        <Tooltip
          labelFormatter={tooltipLabel}
          formatter={(value, name) => {
            if (String(name).includes("Price")) return [formatGbpPerMwh(value), name];
            return [formatKw(value), name];
          }}
        />
        <Legend verticalAlign="top" height={32} />
        <Area
          yAxisId="left"
          type="stepAfter"
          dataKey="optimized_kw"
          name="Optimized site-cap schedule"
          stroke="#4CAF50"
          fill="rgba(76, 175, 80, 0.18)"
          strokeWidth={2.5}
        />
        <Line
          yAxisId="left"
          type="stepAfter"
          dataKey="baseline_kw"
          name="Dumb baseline"
          stroke="#94A3B8"
          strokeDasharray="6 5"
          dot={false}
          strokeWidth={2}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="price_gbp_per_mwh"
          name="Market Price"
          stroke="#1769E0"
          dot={false}
          strokeWidth={2}
        />
        <ReferenceLine
          yAxisId="left"
          y={750}
          label={{ value: "750 kW cap", position: "insideTopRight", fill: "#15803D" }}
          stroke="#4CAF50"
          strokeDasharray="4 4"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function ScheduledActualChart({ data }: { data: DataRecord[] }) {
  return (
    <div className="chart-with-legend">
      <div className="chart-legend compact">
        <span>
          <i style={{ background: "#AAB4C3" }} />
          Deviation MWh
        </span>
        <span>
          <i className="line" style={{ background: "#5CB85C" }} />
          Scheduled MWh
        </span>
        <span>
          <i className="line" style={{ background: "#2563EB" }} />
          Actual MWh
        </span>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={data} margin={{ top: 12, right: 16, bottom: 18, left: 0 }}>
          <CartesianGrid stroke={gridColor} vertical={false} />
          <XAxis
            dataKey="settlement_period"
            tick={axisStyle}
            tickFormatter={(value) => String(Math.round(numeric(value)))}
            minTickGap={10}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={axisStyle}
            width={50}
            domain={[
              (min: number) => Math.min(-0.05, min - 0.02),
              (max: number) => Math.max(0.05, max + 0.06)
            ]}
          />
          <Tooltip
            labelFormatter={tooltipLabel}
            formatter={(value, name) => [
              `${numeric(value).toFixed(4)} MWh`,
              name
            ]}
          />
          <Bar dataKey="deviation_mwh" name="Deviation MWh" fill="#AAB4C3" opacity={0.75} />
          <Line
            type="monotone"
            dataKey="scheduled_mwh"
            name="Scheduled MWh"
            stroke="#5CB85C"
            dot={false}
            strokeWidth={2.2}
          />
          <Line
            type="monotone"
            dataKey="actual_mwh"
            name="Actual MWh"
            stroke="#2563EB"
            dot={false}
            strokeWidth={2.2}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SettlementExposureChart({ data }: { data: DataRecord[] }) {
  return (
    <ResponsiveContainer width="100%" height={310}>
      <ComposedChart data={data} margin={{ top: 18, right: 18, bottom: 18, left: 0 }}>
        <CartesianGrid stroke={gridColor} vertical={false} />
        <XAxis
          dataKey="settlement_period"
          tick={axisStyle}
          tickFormatter={(value) => String(Math.round(numeric(value)))}
        />
        <YAxis yAxisId="left" tick={axisStyle} width={58} tickFormatter={(value) => `£${value}`} />
        <YAxis yAxisId="right" orientation="right" tick={axisStyle} width={58} />
        <Tooltip
          labelFormatter={tooltipLabel}
          formatter={(value, name) => {
            const label = String(name);
            if (label.includes("Price")) return [formatGbpPerMwh(value), name];
            return [formatGbp(value, 2), name];
          }}
        />
        <Legend verticalAlign="top" height={32} />
        <Bar
          yAxisId="right"
          dataKey="imbalance_exposure_gbp"
          name="Deviation Cost"
          fill="#22C7C9"
          opacity={0.72}
        />
        <Line
          yAxisId="left"
          dataKey="scheduled_price_gbp_per_mwh"
          name="Scheduled Price"
          stroke="#2563EB"
          dot={false}
          strokeWidth={2}
        />
        <Line
          yAxisId="left"
          dataKey="imbalance_price_gbp_per_mwh"
          name="Imbalance Price"
          stroke="#F97316"
          dot={false}
          strokeWidth={2}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function CostComparisonChart({ data }: { data: DataRecord[] }) {
  const colors = ["#94A3B8", "#0EA5A4", "#6D4FD3"];
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 18, right: 18, bottom: 46, left: 4 }}>
        <CartesianGrid stroke={gridColor} vertical={false} />
        <XAxis dataKey="cost_type" tick={axisStyle} interval={0} angle={-18} textAnchor="end" />
        <YAxis tick={axisStyle} tickFormatter={(value) => `£${value}`} />
        <Tooltip formatter={(value) => [formatGbp(value, 2), "Cost"]} />
        <Bar dataKey="cost_gbp" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={text(entry.cost_type, String(index))} fill={colors[index % colors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ExceptionsSeverityChart({ data }: { data: DataRecord[] }) {
  const colors: Record<string, string> = {
    critical: "#991B1B",
    high: "#E11D48",
    medium: "#E49A00",
    low: "#1769E0"
  };
  return (
    <ResponsiveContainer width="100%" height={230}>
      <BarChart data={data} margin={{ top: 18, right: 18, bottom: 22, left: 0 }}>
        <CartesianGrid stroke={gridColor} vertical={false} />
        <XAxis dataKey="severity" tick={axisStyle} />
        <YAxis tick={axisStyle} allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
          {data.map((entry) => (
            <Cell key={text(entry.severity)} fill={colors[text(entry.severity).toLowerCase()] || "#64748B"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MarketPriceChart({ data }: { data: DataRecord[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 18, right: 18, bottom: 18, left: 4 }}>
        <CartesianGrid stroke={gridColor} vertical={false} />
        <XAxis
          dataKey="settlement_period"
          tick={axisStyle}
          tickFormatter={(value) => String(Math.round(numeric(value)))}
        />
        <YAxis tick={axisStyle} tickFormatter={(value) => `£${value}`} width={64} />
        <Tooltip
          labelFormatter={tooltipLabel}
          formatter={(value) => [formatGbpPerMwh(value), "Price"]}
        />
        <Legend verticalAlign="top" height={32} />
        <Area
          type="monotone"
          dataKey="price_gbp_per_mwh"
          name="Market Price"
          stroke="#1769E0"
          fill="rgba(23, 105, 224, 0.14)"
          strokeWidth={2.4}
        />
        <ReferenceLine y={0} stroke="#CBD5E1" strokeDasharray="3 3" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
