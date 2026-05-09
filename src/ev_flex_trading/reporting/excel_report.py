"""Professional Excel daily trading report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ev_flex_trading.config import OUTPUTS_DIR, PROJECT_ROOT, ensure_data_directories
from ev_flex_trading.reporting.report_formatting import WorkbookFormats, build_formats
from ev_flex_trading.reporting.report_inputs import ExcelReportInputs, load_excel_report_inputs

WORKBOOK_PATH = OUTPUTS_DIR / "ev_flex_daily_trading_report_sample.xlsx"
MANIFEST_PATH = OUTPUTS_DIR / "phase6_report_manifest_sample.csv"


def generate_excel_report(
    *,
    output_path: Path = WORKBOOK_PATH,
    manifest_path: Path = MANIFEST_PATH,
    auto_generate_inputs: bool = True,
) -> tuple[Path, pd.DataFrame]:
    """Generate the Phase 6 daily trading report workbook."""

    ensure_data_directories()
    inputs, manifest = load_excel_report_inputs(auto_generate=auto_generate_inputs)
    generated_at = datetime.now(timezone.utc).isoformat()

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book
        formats = build_formats(workbook)

        _write_readme(writer, inputs, formats, generated_at)
        _write_daily_summary(writer, inputs, formats)
        _write_baseline_vs_optimized(writer, inputs, formats)
        _write_scheduled_vs_actual(writer, inputs, formats)
        _write_settlement_exposure(writer, inputs, formats)
        _write_market_metrics(writer, inputs, formats)
        _write_exceptions(writer, inputs, formats)
        _write_data_sheet(writer, "Fleet Requirements", inputs.fleet_requirements, formats)
        _write_data_sheet(writer, "Market Prices", inputs.market_prices, formats)
        _write_data_sheet(writer, "Baseline Schedule", inputs.baseline_schedule, formats)
        _write_data_sheet(writer, "Optimized Schedule", inputs.optimized_schedule, formats)
        _write_data_sheet(writer, "Actual Charging", inputs.actual_charging, formats)
        _write_assumptions(writer, inputs, formats)

    manifest = pd.concat(
        [
            manifest,
            pd.DataFrame(
                [
                    {
                        "input_name": "workbook",
                        "path": _display_path(output_path),
                        "rows": "",
                    },
                    {"input_name": "generated_at_utc", "path": generated_at, "rows": ""},
                ]
            ),
        ],
        ignore_index=True,
    )
    manifest.to_csv(manifest_path, index=False)
    return output_path, manifest


def _display_path(path: Path) -> str:
    """Return a repo-relative path when possible, otherwise the file name."""

    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return path.name


def _write_readme(
    writer: pd.ExcelWriter,
    inputs: ExcelReportInputs,
    formats: WorkbookFormats,
    generated_at: str,
) -> None:
    sheet = "README"
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.set_column("A:A", 28)
    worksheet.set_column("B:B", 95)
    worksheet.write("A1", "EV Flex Trading Ops Simulator", formats.title)
    worksheet.write("A2", "Daily Trading Support Report", formats.subtitle)

    base = inputs.daily_summary_base.iloc[0]
    rows = [
        ("Report date", base["service_date"]),
        ("Run ID", base["run_id"]),
        ("Generated at UTC", generated_at),
        ("Data status", "Synthetic/sample public demonstration data"),
        (
            "Purpose",
            "Summarize EV flexibility trading analytics: baseline, optimized schedule, actual charging, reconciliation, settlement-style exposure, and exceptions.",
        ),
        (
            "Important limitation",
            "This workbook is a simplified public demonstration and not a production trading, dispatch, or settlement system.",
        ),
        (
            "Key interpretation",
            "Use Daily Summary for headline metrics, Exceptions for analyst review, and data tabs for traceability.",
        ),
    ]
    for row_idx, (label, value) in enumerate(rows, start=4):
        worksheet.write(row_idx, 0, label, formats.header)
        worksheet.write(row_idx, 1, value, formats.wrapped)

    sheet_descriptions = pd.DataFrame(
        [
            ("Daily Summary", "Executive KPI view and scenario comparison."),
            (
                "Baseline vs Optimized",
                "Immediate-charge baseline versus site-cap optimized charging.",
            ),
            (
                "Scheduled vs Actual",
                "Scheduled position compared with synthetic actual metered charging.",
            ),
            (
                "Settlement Exposure",
                "Simplified settlement-style exposure, not official settlement.",
            ),
            ("Market Metrics", "Trading-support participation and deviation metrics."),
            ("Exceptions", "Analyst review queue."),
            ("Fleet Requirements", "Synthetic fleet requirements and feasibility inputs."),
            ("Market Prices", "Synthetic/sample normalized market prices."),
            ("Baseline Schedule", "Immediate-charge vehicle schedule."),
            ("Optimized Schedule", "Price-optimized vehicle schedule."),
            ("Actual Charging", "Synthetic actual metered charging."),
            ("Assumptions", "Model assumptions, units, and limitations."),
        ],
        columns=["Sheet", "Description"],
    )
    _write_table(writer, "README", sheet_descriptions, 13, 0, "ReadmeSheets", formats)


def _write_daily_summary(
    writer: pd.ExcelWriter, inputs: ExcelReportInputs, formats: WorkbookFormats
) -> None:
    sheet = "Daily Summary"
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.set_column("A:M", 18)
    worksheet.write("A1", "Daily Summary", formats.title)
    worksheet.write(
        "A2", "Primary scenario: base actuals using site-cap optimized schedule", formats.subtitle
    )

    base = inputs.daily_summary_base.iloc[0]
    kpis = [
        ("Scheduled MWh", base["scheduled_mwh"], formats.mwh),
        ("Actual MWh", base["actual_mwh"], formats.mwh),
        ("Deviation MWh", base["deviation_mwh"], formats.mwh),
        ("Settlement-style cost", base["total_settlement_style_cost_gbp"], formats.gbp),
        ("Dumb baseline cost", base["dumb_baseline_cost_gbp"], formats.gbp),
        ("Optimized expected cost", base["optimized_expected_cost_gbp"], formats.gbp),
        ("Realized savings", base["realized_savings_vs_baseline_gbp"], formats.gbp),
        ("Realized savings %", base["realized_savings_vs_baseline_pct"] / 100, formats.pct),
        ("Delta vs optimized", base["delta_vs_optimized_plan_gbp"], formats.gbp),
        ("Readiness %", base["vehicle_readiness_pct"] / 100, formats.pct),
        ("Material deviations", base["material_deviation_intervals"], formats.integer),
        ("Missing meter intervals", base["missing_meter_intervals"], formats.integer),
        ("Exception count", base["exception_count"], formats.integer),
    ]
    for idx, (label, value, value_format) in enumerate(kpis):
        row = 4 + (idx // 4) * 3
        col = (idx % 4) * 3
        worksheet.merge_range(row, col, row, col + 1, label, formats.kpi_label)
        worksheet.merge_range(row + 1, col, row + 1, col + 1, value, value_format)

    summaries = pd.concat([inputs.daily_summary_base, inputs.daily_summary_high], ignore_index=True)
    _write_table(writer, sheet, summaries, 16, 0, "DailySummaryTable", formats)

    chart_data = pd.DataFrame(
        [
            ("Dumb baseline", base["dumb_baseline_cost_gbp"]),
            ("Optimized expected", base["optimized_expected_cost_gbp"]),
            ("Settlement-style actual", base["total_settlement_style_cost_gbp"]),
        ],
        columns=["Cost Type", "GBP"],
    )
    _write_table(writer, sheet, chart_data, 23, 16, "CostBridgeData", formats)
    chart = workbook.add_chart({"type": "column"})
    chart.add_series(
        {
            "name": "Cost comparison",
            "categories": [sheet, 24, 16, 26, 16],
            "values": [sheet, 24, 17, 26, 17],
        }
    )
    chart.set_title({"name": "Cost Comparison"})
    chart.set_y_axis({"name": "GBP"})
    worksheet.insert_chart("Q3", chart, {"x_scale": 1.25, "y_scale": 1.2})


def _write_baseline_vs_optimized(
    writer: pd.ExcelWriter,
    inputs: ExcelReportInputs,
    formats: WorkbookFormats,
) -> None:
    sheet = "Baseline vs Optimized"
    worksheet = writer.book.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.write("A1", "Baseline vs Optimized", formats.title)
    worksheet.write(
        "A2", "Primary optimized scenario uses a 750 kW site import cap.", formats.subtitle
    )
    _write_table(
        writer, sheet, inputs.optimization_summary_site_cap, 4, 0, "OptimizationSummary", formats
    )

    load = _combine_load_profiles(inputs.baseline_schedule, inputs.optimized_schedule)
    _write_table(writer, sheet, load, 10, 0, "LoadProfileComparison", formats)
    chart = writer.book.add_chart({"type": "line"})
    last_row = 10 + len(load)
    chart.add_series(
        {
            "name": "Baseline kW",
            "categories": [sheet, 11, 2, last_row, 2],
            "values": [sheet, 11, 3, last_row, 3],
        }
    )
    chart.add_series(
        {
            "name": "Optimized kW",
            "categories": [sheet, 11, 2, last_row, 2],
            "values": [sheet, 11, 4, last_row, 4],
        }
    )
    chart.set_title({"name": "Baseline vs Optimized Load"})
    chart.set_y_axis({"name": "kW"})
    worksheet.insert_chart("H10", chart, {"x_scale": 1.35, "y_scale": 1.25})


def _write_scheduled_vs_actual(
    writer: pd.ExcelWriter,
    inputs: ExcelReportInputs,
    formats: WorkbookFormats,
) -> None:
    sheet = "Scheduled vs Actual"
    worksheet = writer.book.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.write("A1", "Scheduled vs Actual", formats.title)
    worksheet.write(
        "A2", "Base actuals scenario shown as primary reconciliation view.", formats.subtitle
    )
    status_summary = (
        inputs.reconciliation_base["reconciliation_status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
    )
    _write_table(writer, sheet, status_summary, 4, 0, "ReconciliationStatusSummary", formats)
    _write_table(writer, sheet, inputs.reconciliation_base, 10, 0, "ScheduledActualBase", formats)
    chart = writer.book.add_chart({"type": "line"})
    last_row = 10 + len(inputs.reconciliation_base)
    chart.add_series(
        {
            "name": "Scheduled MWh",
            "categories": [sheet, 11, 5, last_row, 5],
            "values": [sheet, 11, 6, last_row, 6],
        }
    )
    chart.add_series(
        {
            "name": "Actual MWh",
            "categories": [sheet, 11, 5, last_row, 5],
            "values": [sheet, 11, 7, last_row, 7],
        }
    )
    chart.set_title({"name": "Scheduled vs Actual MWh"})
    worksheet.insert_chart("R4", chart, {"x_scale": 1.25, "y_scale": 1.2})


def _write_settlement_exposure(
    writer: pd.ExcelWriter,
    inputs: ExcelReportInputs,
    formats: WorkbookFormats,
) -> None:
    sheet = "Settlement Exposure"
    worksheet = writer.book.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.write("A1", "Simplified Settlement-Style Exposure", formats.title)
    worksheet.write(
        "A2",
        "Not official BSC settlement. Uses synthetic imbalance spread assumptions.",
        formats.subtitle,
    )
    summary = pd.DataFrame(
        [
            ("Scheduled cost", inputs.settlement_base["scheduled_cost_gbp"].sum()),
            ("Imbalance-style exposure", inputs.settlement_base["imbalance_exposure_gbp"].sum()),
            (
                "Total settlement-style cost",
                inputs.settlement_base["total_settlement_style_cost_gbp"].sum(),
            ),
            ("Largest positive deviation MWh", inputs.settlement_base["deviation_mwh"].max()),
            ("Largest negative deviation MWh", inputs.settlement_base["deviation_mwh"].min()),
            (
                "Highest cost interval GBP",
                inputs.settlement_base["total_settlement_style_cost_gbp"].max(),
            ),
        ],
        columns=["Metric", "Value"],
    )
    _write_table(writer, sheet, summary, 4, 0, "SettlementExposureSummary", formats)
    _write_table(writer, sheet, inputs.settlement_base, 13, 0, "SettlementExposureBase", formats)


def _write_market_metrics(
    writer: pd.ExcelWriter, inputs: ExcelReportInputs, formats: WorkbookFormats
) -> None:
    sheet = "Market Metrics"
    worksheet = writer.book.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.write("A1", "Market Participation Metrics", formats.title)
    _write_table(writer, sheet, inputs.market_metrics, 3, 0, "MarketMetrics", formats)


def _write_exceptions(
    writer: pd.ExcelWriter, inputs: ExcelReportInputs, formats: WorkbookFormats
) -> None:
    sheet = "Exceptions"
    worksheet = writer.book.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.write("A1", "Analyst Review Queue", formats.title)
    exceptions = inputs.exceptions.copy()
    if exceptions.empty:
        exceptions = pd.DataFrame(
            [
                {
                    "severity": "low",
                    "category": "none",
                    "entity_id": "",
                    "timestamp": "",
                    "message": "No exceptions.",
                    "suggested_action": "No action required.",
                }
            ]
        )
    _write_table(writer, sheet, exceptions, 3, 0, "ExceptionsTable", formats)
    severity_col = list(exceptions.columns).index("severity")
    first_row = 4
    last_row = first_row + len(exceptions) - 1
    worksheet.conditional_format(
        first_row,
        severity_col,
        last_row,
        severity_col,
        {"type": "text", "criteria": "containing", "value": "critical", "format": formats.critical},
    )
    worksheet.conditional_format(
        first_row,
        severity_col,
        last_row,
        severity_col,
        {"type": "text", "criteria": "containing", "value": "high", "format": formats.high},
    )
    worksheet.conditional_format(
        first_row,
        severity_col,
        last_row,
        severity_col,
        {"type": "text", "criteria": "containing", "value": "medium", "format": formats.medium},
    )
    worksheet.conditional_format(
        first_row,
        severity_col,
        last_row,
        severity_col,
        {"type": "text", "criteria": "containing", "value": "low", "format": formats.low},
    )


def _write_data_sheet(
    writer: pd.ExcelWriter,
    sheet: str,
    frame: pd.DataFrame,
    formats: WorkbookFormats,
) -> None:
    _write_table(writer, sheet, frame, 0, 0, _table_name(sheet), formats)
    worksheet = writer.sheets[sheet]
    worksheet.freeze_panes(1, 0)


def _write_assumptions(
    writer: pd.ExcelWriter, inputs: ExcelReportInputs, formats: WorkbookFormats
) -> None:
    sheet = "Assumptions"
    worksheet = writer.book.add_worksheet(sheet)
    writer.sheets[sheet] = worksheet
    worksheet.set_column("A:A", 32)
    worksheet.set_column("B:B", 100)
    worksheet.write("A1", "Assumptions and Limitations", formats.title)
    assumptions = pd.DataFrame(
        [
            ("Data", "Synthetic EV fleet data and synthetic/sample market prices."),
            (
                "Primary optimized scenario",
                "Site import cap optimized schedule, 750 kW where available.",
            ),
            ("Charging windows", "Arrival rounded up to next half-hour; departure rounded down."),
            ("Charging efficiency", "1.0 in sample workflows unless configured otherwise."),
            ("Actuals", "Synthetic actual charging scenarios for public demonstration."),
            ("Settlement-style exposure", "Simplified spread model; not official BSC settlement."),
            ("P&L-style summary", "Illustrative trading-support summary; not real trading P&L."),
            ("Execution", "No live trading, dispatch, or operational control."),
            ("Units", "kWh/MWh for energy, kW/MW for power, GBP/MWh for prices."),
        ],
        columns=["Topic", "Assumption"],
    )
    _write_table(writer, sheet, assumptions, 3, 0, "AssumptionsTable", formats)


def _write_table(
    writer: pd.ExcelWriter,
    sheet: str,
    frame: pd.DataFrame,
    startrow: int,
    startcol: int,
    table_name: str,
    formats: WorkbookFormats,
) -> None:
    safe = frame.copy()
    safe.to_excel(writer, sheet_name=sheet, startrow=startrow, startcol=startcol, index=False)
    worksheet = writer.sheets[sheet]
    rows, cols = safe.shape
    if rows == 0 or cols == 0:
        return
    worksheet.add_table(
        startrow,
        startcol,
        startrow + rows,
        startcol + cols - 1,
        {
            "name": table_name[:31],
            "columns": [{"header": str(column)} for column in safe.columns],
            "style": "Table Style Medium 2",
        },
    )
    for idx, column in enumerate(safe.columns):
        width = min(
            max(
                len(str(column)) + 2, 12, int(safe[column].astype(str).str.len().quantile(0.9)) + 2
            ),
            35,
        )
        worksheet.set_column(startcol + idx, startcol + idx, width)
        if (
            "notes" in str(column).lower()
            or "message" in str(column).lower()
            or "action" in str(column).lower()
        ):
            worksheet.set_column(
                startcol + idx, startcol + idx, min(max(width, 28), 55), formats.wrapped
            )


def _combine_load_profiles(
    baseline_schedule: pd.DataFrame, optimized_schedule: pd.DataFrame
) -> pd.DataFrame:
    baseline = (
        baseline_schedule.groupby(
            ["settlement_date", "settlement_period", "timestamp"], dropna=False
        )["charge_kwh"]
        .sum()
        .reset_index(name="baseline_kwh")
    )
    optimized = (
        optimized_schedule.groupby(
            ["settlement_date", "settlement_period", "timestamp"], dropna=False
        )["charge_kwh"]
        .sum()
        .reset_index(name="optimized_kwh")
    )
    merged = baseline.merge(
        optimized, on=["settlement_date", "settlement_period", "timestamp"], how="outer"
    ).fillna(0.0)
    merged["baseline_kw"] = merged["baseline_kwh"] / 0.5
    merged["optimized_kw"] = merged["optimized_kwh"] / 0.5
    return merged.sort_values(["settlement_date", "settlement_period"])


def _table_name(sheet: str) -> str:
    return "".join(ch for ch in sheet.title() if ch.isalnum())[:25] + "Table"
