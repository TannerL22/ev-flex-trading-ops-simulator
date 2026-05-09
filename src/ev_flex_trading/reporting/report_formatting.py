"""Formatting helpers for the Excel daily trading report."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkbookFormats:
    title: object
    subtitle: object
    section: object
    header: object
    text: object
    wrapped: object
    kpi_label: object
    kpi_value: object
    gbp: object
    gbp_mwh: object
    mwh: object
    mw: object
    pct: object
    integer: object
    datetime: object
    low: object
    medium: object
    high: object
    critical: object


def build_formats(workbook) -> WorkbookFormats:  # noqa: ANN001
    """Create workbook formats in one place for consistency."""

    return WorkbookFormats(
        title=workbook.add_format({"bold": True, "font_size": 18, "font_color": "#17324d"}),
        subtitle=workbook.add_format({"font_size": 10, "font_color": "#4f5f6f"}),
        section=workbook.add_format(
            {"bold": True, "font_size": 12, "bg_color": "#d9eaf7", "border": 1}
        ),
        header=workbook.add_format(
            {"bold": True, "font_color": "white", "bg_color": "#1f4e79", "border": 1}
        ),
        text=workbook.add_format({"border": 1}),
        wrapped=workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"}),
        kpi_label=workbook.add_format(
            {"bold": True, "font_color": "white", "bg_color": "#1f4e79", "align": "center"}
        ),
        kpi_value=workbook.add_format(
            {"bold": True, "font_size": 14, "bg_color": "#edf4f8", "border": 1, "align": "center"}
        ),
        gbp=workbook.add_format({"num_format": "£#,##0.00", "border": 1}),
        gbp_mwh=workbook.add_format({"num_format": "£#,##0.00", "border": 1}),
        mwh=workbook.add_format({"num_format": "0.000", "border": 1}),
        mw=workbook.add_format({"num_format": "0.0", "border": 1}),
        pct=workbook.add_format({"num_format": "0.0%", "border": 1}),
        integer=workbook.add_format({"num_format": "0", "border": 1}),
        datetime=workbook.add_format({"num_format": "yyyy-mm-dd hh:mm", "border": 1}),
        low=workbook.add_format({"bg_color": "#e2f0d9", "border": 1}),
        medium=workbook.add_format({"bg_color": "#fff2cc", "border": 1}),
        high=workbook.add_format({"bg_color": "#f8cbad", "border": 1}),
        critical=workbook.add_format({"bg_color": "#c00000", "font_color": "white", "border": 1}),
    )
