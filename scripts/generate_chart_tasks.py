#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TASK = ROOT / "template-chart-task"
TASKS_DIR = ROOT / "tasks"

POS = {
    "from": {"cell": "D2", "xOffsetPts": 0, "yOffsetPts": 0},
    "to": {"cell": "J16", "xOffsetPts": 0, "yOffsetPts": 0},
}
SMALL_POS = {
    "from": {"cell": "D2", "xOffsetPts": 0, "yOffsetPts": 0},
    "to": {"cell": "H10", "xOffsetPts": 0, "yOffsetPts": 0},
}
WIDE_POS = {
    "from": {"cell": "B2", "xOffsetPts": 10, "yOffsetPts": 5},
    "to": {"cell": "J12", "xOffsetPts": 40, "yOffsetPts": 20},
}
TALL_POS = {
    "from": {"cell": "D2", "xOffsetPts": 0, "yOffsetPts": 0},
    "to": {"cell": "J24", "xOffsetPts": 0, "yOffsetPts": 0},
}


class Missing:
    pass


MISSING = Missing()


def cells(rows: list[list[Any]], sheet: str = "Sheet1") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        for col_index, value in enumerate(row, start=1):
            if isinstance(value, Missing):
                continue
            col = ""
            index = col_index
            while index:
                index, rem = divmod(index - 1, 26)
                col = chr(ord("A") + rem) + col
            out.append({"address": f"{col}{row_index}", "value": value})
    return out


def case(case_id: str, rows: list[list[Any]], chart: dict[str, Any], sheet: str = "Sheet1") -> dict[str, Any]:
    return {"case_id": case_id, "sheets": [{"name": sheet, "cells": cells(rows, sheet)}], "chart": chart}


def chart(
    name: str,
    group: dict[str, Any],
    *,
    title: str,
    category_title: str | None = "Category",
    value_title: str | None = "Value",
    legend: str = "right",
    position: dict[str, Any] = POS,
    axes: bool = True,
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "name": name,
        "position": position,
        "groups": [group],
        "title": {"text": title},
        "legend": {"position": legend},
    }
    if axes:
        spec["axes"] = {
            "category": {"title": {"text": category_title or "Category"}},
            "value": {"title": {"text": value_title or "Value"}},
        }
    return spec


def series(name_ref: str, categories: str, values: str, **extra: Any) -> dict[str, Any]:
    out = {"name": {"ref": name_ref}, "categories": categories, "values": values}
    out.update(extra)
    return out


def xy_series(name: str, x_values: str, y_values: str, **extra: Any) -> dict[str, Any]:
    out = {"name": {"text": name}, "xValues": x_values, "yValues": y_values}
    out.update(extra)
    return out


def row_range(last: int, col: str = "A") -> str:
    return f"Sheet1!{col}2:{col}{last}"


def common_rows() -> list[list[Any]]:
    return [
        ["Category", "Value", "Other"],
        ["Q1", 12, 5],
        ["Q2", 19, 7],
        ["Q3", 7, 11],
        ["Q4", 15, 9],
    ]


def many_rows(n: int) -> list[list[Any]]:
    rows = [["Label", "Value", "Other"]]
    values = [4, 9, 3, 12, 7, 1, 10, 5, 13, 6, 15, 2]
    other = [2, 5, 8, 4, 11, 6, 1, 9, 3, 12, 7, 10]
    for i in range(n):
        rows.append([f"L{i + 1}", values[i], other[i]])
    return rows


def set_axis_defaults(case_obj: dict[str, Any], defaults: dict[str, Any]) -> None:
    axes = case_obj["chart"].setdefault("axes", {})
    for axis_name, title in (("category", "Category"), ("value", "Value")):
        axis = axes.setdefault(axis_name, {"title": {"text": title}})
        axis.setdefault("title", {"text": title})
        for field, value in defaults.items():
            axis.setdefault(field, value)


def strip_case_id(case_obj: dict[str, Any]) -> dict[str, Any]:
    public_case = dict(case_obj)
    public_case.pop("case_id", None)
    return public_case


def normalize_cases(slug: str, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Make varied settings explicit so the task is not about guessing property names."""
    if slug in {"chart-line", "chart-scatter"}:
        for item in cases:
            group = item["chart"]["groups"][0]
            group.setdefault("smooth", False)
            for ser in group["series"]:
                ser.setdefault("smooth", False)
                ser.setdefault("lineWidth", 2.25)
                ser.setdefault("marker", {"style": "circle", "size": 6})
                if "lineColor" not in ser:
                    ser["lineColor"] = ser.get("fillColor") or "#4472C4"
                if slug == "chart-scatter" and "fillColor" not in ser:
                    ser["fillColor"] = ser.get("lineColor") or "#4472C4"
        if slug == "chart-scatter":
            for item in cases:
                set_axis_defaults(item, {"min": None, "max": None, "majorUnit": None})

    if slug == "chart-bubble":
        for item in cases:
            set_axis_defaults(item, {"min": None, "max": None, "majorUnit": None})

    if slug == "chart-area":
        for item in cases:
            group = item["chart"]["groups"][0]
            for ser in group["series"]:
                ser.setdefault("lineColor", ser.get("fillColor") or "#4472C4")
            item["chart"].setdefault("displayBlanksAs", "gap")

    if slug == "chart-radar":
        for item in cases:
            group = item["chart"]["groups"][0]
            for ser in group["series"]:
                ser.setdefault("lineColor", ser.get("fillColor") or "#4472C4")
                ser.setdefault("marker", {"style": "none" if group.get("radarStyle") != "marker" else "circle", "size": 6})
                ser.setdefault("fillColor", None)

    if slug == "chart-waterfall":
        for item in cases:
            for ser in item["chart"]["groups"][0]["series"]:
                ser.setdefault("fillColor", None)

    if slug in {"chart-bar", "chart-column"}:
        for item in cases:
            group = item["chart"]["groups"][0]
            group.setdefault("gapWidth", 150)
            axes = item["chart"].setdefault("axes", {})
            category_axis = axes.setdefault("category", {"title": {"text": "Category"}})
            category_axis.setdefault("title", {"text": "Category"})
            category_axis.setdefault("reversed", False)
            if slug == "chart-column":
                value_axis = axes.setdefault("value", {"title": {"text": "Value"}})
                value_axis.setdefault("title", {"text": "Value"})
                value_axis.setdefault("min", None)
                value_axis.setdefault("max", None)
                value_axis.setdefault("majorUnit", None)

    if slug in {"chart-histogram", "chart-pareto"}:
        for item in cases:
            for ser in item["chart"]["groups"][0]["series"]:
                options = ser.setdefault("binOptions", {"type": "auto"})
                options.setdefault("allowUnderflow", False)
                options.setdefault("allowOverflow", False)
                options.setdefault("underflowValue", None)
                options.setdefault("overflowValue", None)
                options.setdefault("count", None)
                options.setdefault("width", None)

    return cases


def bar_cases() -> list[dict[str, Any]]:
    base = common_rows()
    return [
        case("basic-horizontal", base, chart("BasicBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4")]}, title="Basic Bar", category_title="Category", value_title="Value")),
        case("negative-and-zero", [["Item", "Delta"], ["Loss", -10], ["Flat", 0], ["Gain", 15], ["Dip", -3]], chart("NegativeBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#ED7D31")]}, title="Negative Bar", category_title="Item", value_title="Delta")),
        case("single-point", [["Item", "Value"], ["Only", 42]], chart("SingleBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", "Sheet1!A2:A2", "Sheet1!B2:B2", fillColor="#70AD47")]}, title="Single Bar", category_title="Item", value_title="Value")),
        case("eight-categories", many_rows(8), chart("EightBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(9), row_range(9, "B"), fillColor="#A5A5A5")]}, title="Eight Bars", category_title="Label", value_title="Value")),
        case("stacked-two-series", base, chart("StackedBar", {"type": "bar", "grouping": "stacked", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4"), series("Sheet1!C1", row_range(5), row_range(5, "C"), fillColor="#ED7D31")]}, title="Stacked Bar", category_title="Category", value_title="Value")),
        case("percent-stacked", base, chart("PercentBar", {"type": "bar", "grouping": "percentStacked", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4"), series("Sheet1!C1", row_range(5), row_range(5, "C"), fillColor="#70AD47")]}, title="Percent Bar", category_title="Category", value_title="Share")),
        case("blank-and-text-values", [["Slot", "Observed"], ["A", 5], ["B", None], ["C", "n/a"], ["D", 12]], chart("BlankBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#5B9BD5")]}, title="Blank Bar", category_title="Slot", value_title="Observed")),
        case("small-position", base, chart("SmallBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4")]}, title="Small Bar", position=SMALL_POS)),
        case("wide-offset-position", base, chart("WideBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4")]}, title="Wide Bar", position=WIDE_POS)),
        case("narrow-gap", base, chart("NarrowGapBar", {"type": "bar", "grouping": "standard", "gapWidth": 50, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#70AD47")]}, title="Narrow Gap")),
        case("wide-gap", base, chart("WideGapBar", {"type": "bar", "grouping": "standard", "gapWidth": 300, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#70AD47")]}, title="Wide Gap")),
        case("twelve-categories", many_rows(12), chart("TwelveBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(13), row_range(13, "B"), fillColor="#4472C4")]}, title="Twelve Bars", category_title="Label", value_title="Value")),
        case("reversed-category-axis", base, chart("ReversedBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#5B9BD5")]}, title="Reversed Bar", category_title="Category", value_title="Value") | {"axes": {"category": {"title": {"text": "Category"}, "reversed": True}, "value": {"title": {"text": "Value"}}}}),
        case("legend-bottom", base, chart("BottomLegendBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#ED7D31")]}, title="Bottom Legend", legend="bottom")),
        case("custom-fill", base, chart("CustomFillBar", {"type": "bar", "grouping": "standard", "gapWidth": 150, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#7030A0")]}, title="Custom Fill")),
    ]


def line_cases() -> list[dict[str, Any]]:
    base = common_rows()
    marker = {"style": "circle", "size": 6}
    return [
        case("basic-line", base, chart("BasicLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", lineWidth=2.25, marker=marker)]}, title="Basic Line")),
        case("negative-crossing", [["Month", "Delta"], ["Jan", -4], ["Feb", 0], ["Mar", 8], ["Apr", -2], ["May", 13]], chart("NegativeLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#ED7D31", lineWidth=2.25, marker=marker)]}, title="Negative Line", category_title="Month", value_title="Delta")),
        case("flat-line", [["Bucket", "Level"], ["A", 5], ["B", 5], ["C", 5], ["D", 5]], chart("FlatLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#70AD47", lineWidth=2.25, marker=marker)]}, title="Flat Line")),
        case("single-point", [["Item", "Value"], ["Only", 42]], chart("SingleLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", "Sheet1!A2:A2", "Sheet1!B2:B2", lineColor="#5B9BD5", lineWidth=2.25, marker=marker)]}, title="Single Point")),
        case("twelve-points", many_rows(12), chart("TwelveLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(13), row_range(13, "B"), lineColor="#A5A5A5", lineWidth=2.25, marker=marker)]}, title="Twelve Points")),
        case("stacked-two-series", base, chart("StackedLine", {"type": "line", "grouping": "stacked", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", marker=marker), series("Sheet1!C1", row_range(5), row_range(5, "C"), lineColor="#ED7D31", marker={"style": "square", "size": 6})]}, title="Stacked Line")),
        case("percent-stacked-two-series", base, chart("PercentLine", {"type": "line", "grouping": "percentStacked", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", marker=marker), series("Sheet1!C1", row_range(5), row_range(5, "C"), lineColor="#70AD47", marker={"style": "square", "size": 6})]}, title="Percent Line")),
        case("blank-and-text-values", [["Step", "Reading"], ["One", 7], ["Two", None], ["Three", "n/a"], ["Four", 11]], chart("BlankLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", marker=marker)]}, title="Blank Line")),
        case("smooth-line", base, chart("SmoothLine", {"type": "line", "grouping": "standard", "smooth": True, "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#7030A0", lineWidth=2.25, smooth=True, marker=marker)]}, title="Smooth Line")),
        case("no-marker-line", base, chart("NoMarkerLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", lineWidth=2.25, marker={"style": "none", "size": 6})]}, title="No Marker Line")),
        case("wide-line", base, chart("WideLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#FFC000", lineWidth=4.5, marker=marker)]}, title="Wide Line")),
        case("legend-bottom", base, chart("BottomLegendLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", marker=marker)]}, title="Bottom Legend", legend="bottom")),
        case("small-position", base, chart("SmallLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#4472C4", marker=marker)]}, title="Small Line", position=SMALL_POS)),
        case("long-text", [["Long Category", "Long Measure"], ["Alpha", 4], ["Bravo", 9], ["Charlie", 2], ["Delta", 7]], chart("LongTextLine", {"type": "line", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), lineColor="#5B9BD5", marker=marker)]}, title="Long Settings Title for Line Chart", category_title="Long Category Axis Title", value_title="Long Value Axis Title")),
    ]


def area_cases() -> list[dict[str, Any]]:
    base = common_rows()
    return [
        case("basic-area", base, chart("BasicArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4", lineColor="#2F5597")]}, title="Basic Area")),
        case("negative-area", [["Month", "Delta"], ["Jan", -4], ["Feb", 0], ["Mar", 8], ["Apr", -2]], chart("NegativeArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#ED7D31", lineColor="#C55A11")]}, title="Negative Area")),
        case("single-point", [["Item", "Value"], ["Only", 42]], chart("SingleArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", "Sheet1!A2:A2", "Sheet1!B2:B2", fillColor="#70AD47", lineColor="#548235")]}, title="Single Area")),
        case("many-points", many_rows(12), chart("ManyArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(13), row_range(13, "B"), fillColor="#A5A5A5", lineColor="#7F7F7F")]}, title="Many Points")),
        case("stacked-two-series", base, chart("StackedArea", {"type": "area", "grouping": "stacked", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4"), series("Sheet1!C1", row_range(5), row_range(5, "C"), fillColor="#ED7D31")]}, title="Stacked Area")),
        case("percent-stacked", base, chart("PercentArea", {"type": "area", "grouping": "percentStacked", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4"), series("Sheet1!C1", row_range(5), row_range(5, "C"), fillColor="#70AD47")]}, title="Percent Area")),
        case("mixed-sign-stacked", [["Category", "Value", "Other"], ["Q1", 12, -5], ["Q2", -19, 7], ["Q3", 7, -11], ["Q4", 15, 9]], chart("MixedSignArea", {"type": "area", "grouping": "stacked", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4"), series("Sheet1!C1", row_range(5), row_range(5, "C"), fillColor="#ED7D31")]}, title="Mixed Sign Area")),
        case("all-zero-stacked", [["Category", "Value", "Other"], ["Q1", 0, 0], ["Q2", 0, 0], ["Q3", 0, 0], ["Q4", 0, 0]], chart("AllZeroArea", {"type": "area", "grouping": "stacked", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4"), series("Sheet1!C1", row_range(5), row_range(5, "C"), fillColor="#70AD47")]}, title="All Zero Area")),
        case("blank-values", [["Slot", "Observed"], ["A", 5], ["B", None], ["C", MISSING], ["D", 12]], chart("BlankArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#5B9BD5")]}, title="Blank Area")),
        case("blank-values-as-zero", [["Slot", "Observed"], ["A", 5], ["B", None], ["C", MISSING], ["D", 12]], chart("BlankZeroArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#5B9BD5")]}, title="Blank Zero Area") | {"displayBlanksAs": "zero"}),
        case("small-position", base, chart("SmallArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#4472C4")]}, title="Small Area", position=SMALL_POS)),
        case("legend-bottom", base, chart("BottomLegendArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#ED7D31")]}, title="Bottom Legend", legend="bottom")),
        case("custom-fill", base, chart("CustomFillArea", {"type": "area", "grouping": "standard", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#7030A0")]}, title="Custom Fill")),
    ]


COLUMN_CASES_JSON = r'[{"case_id":"quarters-basic","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Quarter"},{"address":"B1","value":"Sales"},{"address":"A2","value":"Q1"},{"address":"B2","value":12},{"address":"A3","value":"Q2"},{"address":"B3","value":19},{"address":"A4","value":"Q3"},{"address":"B4","value":7},{"address":"A5","value":"Q4"},{"address":"B5","value":15}]}],"chart":{"name":"SalesColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Quarterly Sales"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Quarter"}},"value":{"title":{"text":"Sales"}}}}},{"case_id":"months-increasing","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Month"},{"address":"B1","value":"Bookings"},{"address":"A2","value":"Jan"},{"address":"B2","value":3},{"address":"A3","value":"Feb"},{"address":"B3","value":6},{"address":"A4","value":"Mar"},{"address":"B4","value":9},{"address":"A5","value":"Apr"},{"address":"B5","value":12}]}],"chart":{"name":"BookingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#70AD47"}]}],"title":{"text":"Monthly Bookings"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Month"}},"value":{"title":{"text":"Bookings"}}}}},{"case_id":"regions-negative","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Region"},{"address":"B1","value":"Delta"},{"address":"A2","value":"North"},{"address":"B2","value":-4},{"address":"A3","value":"South"},{"address":"B3","value":0},{"address":"A4","value":"East"},{"address":"B4","value":8},{"address":"A5","value":"West"},{"address":"B5","value":13}]}],"chart":{"name":"DeltaColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#ED7D31"}]}],"title":{"text":"Regional Delta"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Region"}},"value":{"title":{"text":"Delta"}}}}},{"case_id":"letters-decimal","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Bucket"},{"address":"B1","value":"Ratio"},{"address":"A2","value":"A"},{"address":"B2","value":1.5},{"address":"A3","value":"B"},{"address":"B3","value":2.25},{"address":"A4","value":"C"},{"address":"B4","value":3.75},{"address":"A5","value":"D"},{"address":"B5","value":2.5}]}],"chart":{"name":"RatioColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#5B9BD5"}]}],"title":{"text":"Bucket Ratios"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Bucket"}},"value":{"title":{"text":"Ratio"}}}}},{"case_id":"years-large","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Year"},{"address":"B1","value":"Revenue"},{"address":"A2","value":"FY21"},{"address":"B2","value":1200},{"address":"A3","value":"FY22"},{"address":"B3","value":980},{"address":"A4","value":"FY23"},{"address":"B4","value":1430},{"address":"A5","value":"FY24"},{"address":"B5","value":760}]}],"chart":{"name":"RevenueColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#A5A5A5"}]}],"title":{"text":"Annual Revenue"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Year"}},"value":{"title":{"text":"Revenue"}}}}},{"case_id":"names-mixed","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Name"},{"address":"B1","value":"Score"},{"address":"A2","value":"Alpha"},{"address":"B2","value":0.2},{"address":"A3","value":"Bravo"},{"address":"B3","value":5.8},{"address":"A4","value":"Charlie"},{"address":"B4","value":1.1},{"address":"A5","value":"Delta"},{"address":"B5","value":9.4}]}],"chart":{"name":"ScoreColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#FFC000"}]}],"title":{"text":"Score Distribution"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Name"}},"value":{"title":{"text":"Score"}}}}},{"case_id":"single-point","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Item"},{"address":"B1","value":"Value"},{"address":"A2","value":"Only"},{"address":"B2","value":42}]}],"chart":{"name":"SinglePointColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A2","values":"Sheet1!B2:B2","fillColor":"#4472C4"}]}],"title":{"text":"Single Point"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Item"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"two-points-opposite","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"State"},{"address":"B1","value":"Delta"},{"address":"A2","value":"Loss"},{"address":"B2","value":-10},{"address":"A3","value":"Gain"},{"address":"B3","value":15}]}],"chart":{"name":"OppositeColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A3","values":"Sheet1!B2:B3","fillColor":"#ED7D31"}]}],"title":{"text":"Opposite Signs"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"State"}},"value":{"title":{"text":"Delta"}}}}},{"case_id":"three-points-flat","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Bucket"},{"address":"B1","value":"Level"},{"address":"A2","value":"A"},{"address":"B2","value":5},{"address":"A3","value":"B"},{"address":"B3","value":5},{"address":"A4","value":"C"},{"address":"B4","value":5}]}],"chart":{"name":"FlatColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A4","values":"Sheet1!B2:B4","fillColor":"#70AD47"}]}],"title":{"text":"Flat Levels"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Bucket"}},"value":{"title":{"text":"Level"}}}}},{"case_id":"five-categories","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Period"},{"address":"B1","value":"Measure"},{"address":"A2","value":"P1"},{"address":"B2","value":2},{"address":"A3","value":"P2"},{"address":"B3","value":8},{"address":"A4","value":"P3"},{"address":"B4","value":1},{"address":"A5","value":"P4"},{"address":"B5","value":10},{"address":"A6","value":"P5"},{"address":"B6","value":6}]}],"chart":{"name":"FiveColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A6","values":"Sheet1!B2:B6","fillColor":"#5B9BD5"}]}],"title":{"text":"Five Categories"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Period"}},"value":{"title":{"text":"Measure"}}}}},{"case_id":"eight-categories","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Label"},{"address":"B1","value":"Count"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":3},{"address":"A5","value":"D"},{"address":"B5","value":12},{"address":"A6","value":"E"},{"address":"B6","value":7},{"address":"A7","value":"F"},{"address":"B7","value":1},{"address":"A8","value":"G"},{"address":"B8","value":10},{"address":"A9","value":"H"},{"address":"B9","value":5}]}],"chart":{"name":"EightColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A9","values":"Sheet1!B2:B9","fillColor":"#A5A5A5"}]}],"title":{"text":"Eight Categories"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Label"}},"value":{"title":{"text":"Count"}}}}},{"case_id":"twelve-categories","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Month"},{"address":"B1","value":"Units"},{"address":"A2","value":"Jan"},{"address":"B2","value":13},{"address":"A3","value":"Feb"},{"address":"B3","value":8},{"address":"A4","value":"Mar"},{"address":"B4","value":16},{"address":"A5","value":"Apr"},{"address":"B5","value":4},{"address":"A6","value":"May"},{"address":"B6","value":20},{"address":"A7","value":"Jun"},{"address":"B7","value":11},{"address":"A8","value":"Jul"},{"address":"B8","value":6},{"address":"A9","value":"Aug"},{"address":"B9","value":18},{"address":"A10","value":"Sep"},{"address":"B10","value":2},{"address":"A11","value":"Oct"},{"address":"B11","value":15},{"address":"A12","value":"Nov"},{"address":"B12","value":9},{"address":"A13","value":"Dec"},{"address":"B13","value":22}]}],"chart":{"name":"TwelveColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A13","values":"Sheet1!B2:B13","fillColor":"#4472C4"}]}],"title":{"text":"Twelve Categories"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Month"}},"value":{"title":{"text":"Units"}}}}},{"case_id":"all-zero","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Part"},{"address":"B1","value":"Amount"},{"address":"A2","value":"A"},{"address":"B2","value":0},{"address":"A3","value":"B"},{"address":"B3","value":0},{"address":"A4","value":"C"},{"address":"B4","value":0},{"address":"A5","value":"D"},{"address":"B5","value":0}]}],"chart":{"name":"ZeroColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#70AD47"}]}],"title":{"text":"All Zero"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Part"}},"value":{"title":{"text":"Amount"}}}}},{"case_id":"all-negative","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Item"},{"address":"B1","value":"Loss"},{"address":"A2","value":"A"},{"address":"B2","value":-1},{"address":"A3","value":"B"},{"address":"B3","value":-3},{"address":"A4","value":"C"},{"address":"B4","value":-8},{"address":"A5","value":"D"},{"address":"B5","value":-2}]}],"chart":{"name":"NegativeColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#ED7D31"}]}],"title":{"text":"All Negative"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Item"}},"value":{"title":{"text":"Loss"}}}}},{"case_id":"tiny-decimals","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Sample"},{"address":"B1","value":"Rate"},{"address":"A2","value":"S1"},{"address":"B2","value":0.001},{"address":"A3","value":"S2"},{"address":"B3","value":0.0045},{"address":"A4","value":"S3"},{"address":"B4","value":0.002},{"address":"A5","value":"S4"},{"address":"B5","value":0.0075}]}],"chart":{"name":"TinyColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#5B9BD5"}]}],"title":{"text":"Tiny Decimals"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Sample"}},"value":{"title":{"text":"Rate"}}}}},{"case_id":"huge-values","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Site"},{"address":"B1","value":"Volume"},{"address":"A2","value":"A"},{"address":"B2","value":1250000},{"address":"A3","value":"B"},{"address":"B3","value":9800000},{"address":"A4","value":"C"},{"address":"B4","value":4300000},{"address":"A5","value":"D"},{"address":"B5","value":15600000}]}],"chart":{"name":"HugeColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#A5A5A5"}]}],"title":{"text":"Huge Values"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Site"}},"value":{"title":{"text":"Volume"}}}}},{"case_id":"mixed-extreme","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Scenario"},{"address":"B1","value":"Net"},{"address":"A2","value":"Low"},{"address":"B2","value":-2500000},{"address":"A3","value":"Mid"},{"address":"B3","value":500},{"address":"A4","value":"High"},{"address":"B4","value":12500000},{"address":"A5","value":"Zero"},{"address":"B5","value":0}]}],"chart":{"name":"ExtremeColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#FFC000"}]}],"title":{"text":"Mixed Extreme"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Scenario"}},"value":{"title":{"text":"Net"}}}}},{"case_id":"blank-and-missing-values","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Slot"},{"address":"B1","value":"Observed"},{"address":"A2","value":"A"},{"address":"B2","value":5},{"address":"A3","value":"B"},{"address":"B3","value":null},{"address":"A4","value":"C"},{"address":"A5","value":"D"},{"address":"B5","value":12}]}],"chart":{"name":"BlankColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Blank Values"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Slot"}},"value":{"title":{"text":"Observed"}}}}},{"case_id":"text-in-value-range","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Step"},{"address":"B1","value":"Reading"},{"address":"A2","value":"One"},{"address":"B2","value":7},{"address":"A3","value":"Two"},{"address":"B3","value":"n/a"},{"address":"A4","value":"Three"},{"address":"B4","value":3},{"address":"A5","value":"Four"},{"address":"B5","value":11}]}],"chart":{"name":"TextValueColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#70AD47"}]}],"title":{"text":"Text in Values"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Step"}},"value":{"title":{"text":"Reading"}}}}},{"case_id":"boolean-values","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Flag"},{"address":"B1","value":"Count"},{"address":"A2","value":"TrueA"},{"address":"B2","value":true},{"address":"A3","value":"FalseB"},{"address":"B3","value":false},{"address":"A4","value":"NumC"},{"address":"B4","value":2},{"address":"A5","value":"NumD"},{"address":"B5","value":4}]}],"chart":{"name":"BooleanColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#5B9BD5"}]}],"title":{"text":"Boolean Values"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Flag"}},"value":{"title":{"text":"Count"}}}}},{"case_id":"settings-small-chart","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"SmallSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"H10","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Small Chart"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-wide-offset-chart","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"WideOffsetSettingsColumn","position":{"from":{"cell":"B2","xOffsetPts":10,"yOffsetPts":5},"to":{"cell":"J12","xOffsetPts":40,"yOffsetPts":20}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Wide Offset Chart"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-tall-chart","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"TallSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J24","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Tall Chart"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-gap-narrow","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"NarrowGapSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":50,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#70AD47"}]}],"title":{"text":"Narrow Gap"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-gap-wide","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"WideGapSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":300,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#70AD47"}]}],"title":{"text":"Wide Gap"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-legend-bottom","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"BottomLegendSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#ED7D31"}]}],"title":{"text":"Bottom Legend"},"legend":{"position":"bottom"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-legend-top","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"TopLegendSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#ED7D31"}]}],"title":{"text":"Top Legend"},"legend":{"position":"top"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-legend-left","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"LeftLegendSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#ED7D31"}]}],"title":{"text":"Left Legend"},"legend":{"position":"left"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-long-text","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Long Measure"},{"address":"A2","value":"Alpha"},{"address":"B2","value":4},{"address":"A3","value":"Bravo"},{"address":"B3","value":9},{"address":"A4","value":"Charlie"},{"address":"B4","value":2},{"address":"A5","value":"Delta"},{"address":"B5","value":7}]}],"chart":{"name":"LongTextSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#5B9BD5"}]}],"title":{"text":"Long Settings Title for Column Chart"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Long Category Axis Title"}},"value":{"title":{"text":"Long Value Axis Title"}}}}},{"case_id":"settings-minimal-title-text","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"MinimalTitleSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#FFC000"}]}],"title":{"text":"."},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"."}},"value":{"title":{"text":"."}}}}},{"case_id":"settings-custom-fill-color","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"A2","value":"A"},{"address":"B2","value":4},{"address":"A3","value":"B"},{"address":"B3","value":9},{"address":"A4","value":"C"},{"address":"B4","value":2},{"address":"A5","value":"D"},{"address":"B5","value":7}]}],"chart":{"name":"CustomFillSettingsColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#7030A0"}]}],"title":{"text":"Custom Fill Color"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"stacked-two-series","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"C1","value":"Other"},{"address":"A2","value":"Q1"},{"address":"B2","value":12},{"address":"C2","value":5},{"address":"A3","value":"Q2"},{"address":"B3","value":19},{"address":"C3","value":7},{"address":"A4","value":"Q3"},{"address":"B4","value":7},{"address":"C4","value":11},{"address":"A5","value":"Q4"},{"address":"B5","value":15},{"address":"C5","value":9}]}],"chart":{"name":"StackedColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"stacked","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"},{"name":{"ref":"Sheet1!C1"},"categories":"Sheet1!A2:A5","values":"Sheet1!C2:C5","fillColor":"#ED7D31"}]}],"title":{"text":"Stacked Column"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"percent-stacked-two-series","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"C1","value":"Other"},{"address":"A2","value":"Q1"},{"address":"B2","value":12},{"address":"C2","value":5},{"address":"A3","value":"Q2"},{"address":"B3","value":19},{"address":"C3","value":7},{"address":"A4","value":"Q3"},{"address":"B4","value":7},{"address":"C4","value":11},{"address":"A5","value":"Q4"},{"address":"B5","value":15},{"address":"C5","value":9}]}],"chart":{"name":"PercentStackedColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"percentStacked","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"},{"name":{"ref":"Sheet1!C1"},"categories":"Sheet1!A2:A5","values":"Sheet1!C2:C5","fillColor":"#ED7D31"}]}],"title":{"text":"Percent Stacked Column"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}},{"case_id":"settings-reversed-category-axis","sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Category"},{"address":"B1","value":"Value"},{"address":"C1","value":"Other"},{"address":"A2","value":"Q1"},{"address":"B2","value":12},{"address":"C2","value":5},{"address":"A3","value":"Q2"},{"address":"B3","value":19},{"address":"C3","value":7},{"address":"A4","value":"Q3"},{"address":"B4","value":7},{"address":"C4","value":11},{"address":"A5","value":"Q4"},{"address":"B5","value":15},{"address":"C5","value":9}]}],"chart":{"name":"ReversedAxisColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Reversed Axis Column"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"},"reversed":true},"value":{"title":{"text":"Value"},"min":0,"max":25,"majorUnit":5}}}}]'


def column_cases() -> list[dict[str, Any]]:
    return json.loads(COLUMN_CASES_JSON)


def pie_like_cases(kind: str) -> list[dict[str, Any]]:
    title_kind = "Doughnut" if kind == "doughnut" else "Pie"
    base_group: dict[str, Any] = {"type": kind, "firstSliceAngle": 0, "varyColors": True}
    if kind == "doughnut":
        base_group["holeSize"] = 50

    def g(**extra: Any) -> dict[str, Any]:
        group = {**base_group, **extra}
        group["series"] = [series("Sheet1!B1", row_range(5), row_range(5, "B"))]
        return group

    rows = [["Segment", "Share"], ["A", 12], ["B", 19], ["C", 7], ["D", 15]]
    return [
        case("basic", rows, chart(f"Basic{title_kind}", g(), title=f"Basic {title_kind}", legend="right", axes=False)),
        case("dominant-slice", [["Segment", "Share"], ["Core", 80], ["A", 5], ["B", 10], ["C", 5]], chart(f"Dominant{title_kind}", g(), title=f"Dominant {title_kind}", axes=False)),
        case("single-slice", [["Segment", "Share"], ["Only", 42]], chart(f"Single{title_kind}", {**base_group, "series": [series("Sheet1!B1", "Sheet1!A2:A2", "Sheet1!B2:B2")]}, title=f"Single {title_kind}", axes=False)),
        case("many-slices", many_rows(8), chart(f"Many{title_kind}", {**base_group, "series": [series("Sheet1!B1", row_range(9), row_range(9, "B"))]}, title=f"Many {title_kind}", axes=False)),
        case("zero-slice", [["Segment", "Share"], ["A", 12], ["B", 0], ["C", 7], ["D", 15]], chart(f"Zero{title_kind}", g(), title=f"Zero {title_kind}", axes=False)),
        case("negative-slice", [["Segment", "Share"], ["A", 12], ["B", -4], ["C", 7], ["D", 15]], chart(f"Negative{title_kind}", g(), title=f"Negative {title_kind}", axes=False)),
        case("blank-text-slice", [["Segment", "Share"], ["A", 12], ["B", None], ["C", "n/a"], ["D", 15]], chart(f"BlankText{title_kind}", g(), title=f"Blank Text {title_kind}", axes=False)),
        case("single-color", rows, chart(f"SingleColor{title_kind}", g(varyColors=False), title=f"Single Color {title_kind}", axes=False)),
        case("first-slice-90", rows, chart(f"Rotated{title_kind}", g(firstSliceAngle=90), title=f"Rotated {title_kind}", axes=False)),
        case("legend-bottom", rows, chart(f"BottomLegend{title_kind}", g(), title=f"Bottom Legend {title_kind}", legend="bottom", axes=False)),
        case("small-position", rows, chart(f"Small{title_kind}", g(), title=f"Small {title_kind}", position=SMALL_POS, axes=False)),
        case("wide-offset-position", rows, chart(f"Wide{title_kind}", g(), title=f"Wide {title_kind}", position=WIDE_POS, axes=False)),
        case("minimal-title", rows, chart(f"MinimalTitle{title_kind}", g(), title=".", axes=False)),
    ] + ([
        case("hole-size-25", rows, chart("SmallHoleDoughnut", g(holeSize=25), title="Small Hole Doughnut", axes=False)),
        case("hole-size-70", rows, chart("LargeHoleDoughnut", g(holeSize=70), title="Large Hole Doughnut", axes=False)),
    ] if kind == "doughnut" else [])


def scatter_cases() -> list[dict[str, Any]]:
    rows = [["X", "Y", "Y2"], [1, 4, 8], [2, 9, 3], [3, 2, 6], [4, 7, 1]]
    return [
        case("markers-basic", rows, chart("ScatterMarkers", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), marker={"style": "circle", "size": 6}, fillColor="#4472C4")]}, title="Scatter Markers", category_title="X", value_title="Y")),
        case("line-marker", rows, chart("ScatterLineMarker", {"type": "scatter", "scatterStyle": "lineMarker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), lineColor="#ED7D31", lineWidth=2.25, marker={"style": "circle", "size": 6})]}, title="Scatter Line", category_title="X", value_title="Y")),
        case("smooth-line", rows, chart("ScatterSmooth", {"type": "scatter", "scatterStyle": "smoothMarker", "smooth": True, "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), lineColor="#70AD47", smooth=True, marker={"style": "circle", "size": 6})]}, title="Smooth Scatter", category_title="X", value_title="Y")),
        case("line-no-markers", rows, chart("ScatterLineNoMarkers", {"type": "scatter", "scatterStyle": "line", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), lineColor="#4472C4", lineWidth=2.25, marker={"style": "none", "size": 6})]}, title="Scatter Line No Markers", category_title="X", value_title="Y")),
        case("large-markers", rows, chart("ScatterLargeMarkers", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), marker={"style": "circle", "size": 12}, fillColor="#7030A0")]}, title="Large Marker Scatter", category_title="X", value_title="Y")),
        case("negative-x-y", [["X", "Y"], [-3, 4], [-1, -2], [0, 0], [2, 7], [4, -3]], chart("ScatterNegative", {"type": "scatter", "scatterStyle": "lineMarker", "series": [xy_series("Series 1", row_range(6), row_range(6, "B"), lineColor="#4472C4", marker={"style": "circle", "size": 6})]}, title="Negative Scatter", category_title="X", value_title="Y")),
        case("duplicate-x", [["X", "Y"], [1, 4], [1, 8], [2, 3], [4, 9]], chart("ScatterDuplicateX", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), marker={"style": "circle", "size": 6}, fillColor="#5B9BD5")]}, title="Duplicate X", category_title="X", value_title="Y")),
        case("single-point", [["X", "Y"], [2, 9]], chart("ScatterSingle", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", "Sheet1!A2:A2", "Sheet1!B2:B2", marker={"style": "circle", "size": 6}, fillColor="#A5A5A5")]}, title="Single Scatter", category_title="X", value_title="Y")),
        case("two-series", rows, chart("ScatterTwoSeries", {"type": "scatter", "scatterStyle": "lineMarker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), lineColor="#4472C4", marker={"style": "circle", "size": 6}), xy_series("Series 2", row_range(5), row_range(5, "C"), lineColor="#ED7D31", marker={"style": "square", "size": 6})]}, title="Two Series Scatter", category_title="X", value_title="Y")),
        case("blank-values", [["X", "Y"], [1, 4], [2, None], [3, 2], [4, MISSING]], chart("ScatterBlanks", {"type": "scatter", "scatterStyle": "lineMarker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), lineColor="#7030A0", marker={"style": "circle", "size": 6})]}, title="Blank Scatter", category_title="X", value_title="Y")),
        case("axis-fixed-range", rows, chart("ScatterFixedAxis", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), marker={"style": "circle", "size": 6}, fillColor="#4472C4")]}, title="Fixed Axis Scatter", category_title="X", value_title="Y") | {"axes": {"category": {"title": {"text": "X"}, "min": 0, "max": 5, "majorUnit": 1}, "value": {"title": {"text": "Y"}, "min": 0, "max": 10, "majorUnit": 2}}}),
        case("axis-negative-fixed-range", [["X", "Y"], [-5, -10], [-2, 6], [0, 0], [4, -4]], chart("ScatterNegativeFixedAxis", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), marker={"style": "circle", "size": 6}, fillColor="#ED7D31")]}, title="Negative Fixed Axis Scatter", category_title="X", value_title="Y") | {"axes": {"category": {"title": {"text": "X"}, "min": -6, "max": 6, "majorUnit": 2}, "value": {"title": {"text": "Y"}, "min": -12, "max": 8, "majorUnit": 4}}}),
        case("small-position", rows, chart("SmallScatter", {"type": "scatter", "scatterStyle": "marker", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), marker={"style": "circle", "size": 6}, fillColor="#4472C4")]}, title="Small Scatter", position=SMALL_POS, category_title="X", value_title="Y")),
    ]


def bubble_cases() -> list[dict[str, Any]]:
    rows = [["X", "Y", "Size"], [1, 4, 8], [2, 9, 20], [3, 2, 12], [4, 7, 4]]
    def bg(**extra: Any) -> dict[str, Any]:
        return {"type": "bubble", "bubbleScale": 100, "showNegativeBubbles": False, "sizeRepresents": "area", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), bubbleSizes=row_range(5, "C"), fillColor="#4472C4")], **extra}

    return [
        case("basic-bubble", rows, chart("BasicBubble", bg(), title="Basic Bubble", category_title="X", value_title="Y")),
        case("negative-x-y", [["X", "Y", "Size"], [-3, 4, 8], [-1, -2, 20], [0, 0, 12], [2, 7, 4]], chart("NegativeBubble", bg(), title="Negative Bubble", category_title="X", value_title="Y")),
        case("zero-size", [["X", "Y", "Size"], [1, 4, 8], [2, 9, 0], [3, 2, 12], [4, 7, 4]], chart("ZeroSizeBubble", bg(), title="Zero Size Bubble", category_title="X", value_title="Y")),
        case("negative-size-hidden", [["X", "Y", "Size"], [1, 4, 8], [2, 9, -20], [3, 2, 12], [4, 7, 4]], chart("NegativeSizeHiddenBubble", bg(showNegativeBubbles=False), title="Negative Hidden", category_title="X", value_title="Y")),
        case("negative-size-shown", [["X", "Y", "Size"], [1, 4, 8], [2, 9, -20], [3, 2, 12], [4, 7, 4]], chart("NegativeSizeShownBubble", bg(showNegativeBubbles=True), title="Negative Shown", category_title="X", value_title="Y")),
        case("scale-25", rows, chart("Scale25Bubble", bg(bubbleScale=25), title="Scale 25 Bubble", category_title="X", value_title="Y")),
        case("scale-300", rows, chart("Scale300Bubble", bg(bubbleScale=300), title="Scale 300 Bubble", category_title="X", value_title="Y")),
        case("size-width", rows, chart("WidthBubble", bg(sizeRepresents="width"), title="Width Bubble", category_title="X", value_title="Y")),
        case("two-series", [["X", "Y1", "S1", "Y2", "S2"], [1, 4, 8, 8, 10], [2, 9, 20, 3, 5], [3, 2, 12, 6, 18], [4, 7, 4, 1, 8]], chart("TwoSeriesBubble", {"type": "bubble", "bubbleScale": 100, "showNegativeBubbles": False, "sizeRepresents": "area", "series": [xy_series("Series 1", row_range(5), row_range(5, "B"), bubbleSizes=row_range(5, "C"), fillColor="#4472C4"), xy_series("Series 2", row_range(5), row_range(5, "D"), bubbleSizes=row_range(5, "E"), fillColor="#ED7D31")]}, title="Two Series Bubble", category_title="X", value_title="Y")),
        case("blank-size-values", [["X", "Y", "Size"], [1, 4, 8], [2, 9, None], [3, 2, "n/a"], [4, 7, 4]], chart("BlankSizeBubble", bg(), title="Blank Size Bubble", category_title="X", value_title="Y")),
        case("fixed-axis", rows, chart("FixedAxisBubble", bg(), title="Fixed Axis Bubble", category_title="X", value_title="Y") | {"axes": {"category": {"title": {"text": "X"}, "min": 0, "max": 5, "majorUnit": 1}, "value": {"title": {"text": "Y"}, "min": 0, "max": 10, "majorUnit": 2}}}),
        case("single-point", [["X", "Y", "Size"], [2, 9, 20]], chart("SingleBubble", {"type": "bubble", "bubbleScale": 100, "showNegativeBubbles": False, "sizeRepresents": "area", "series": [xy_series("Series 1", "Sheet1!A2:A2", "Sheet1!B2:B2", bubbleSizes="Sheet1!C2:C2", fillColor="#70AD47")]}, title="Single Bubble", category_title="X", value_title="Y")),
        case("small-position", rows, chart("SmallBubble", bg(), title="Small Bubble", position=SMALL_POS, category_title="X", value_title="Y")),
    ]


def radar_cases() -> list[dict[str, Any]]:
    rows = [["Metric", "A", "B"], ["Speed", 10, 7], ["Power", 6, 12], ["Range", 8, 9], ["Cost", 4, 5], ["Quality", 9, 6]]
    return [
        case("standard-radar", rows, chart("StandardRadar", {"type": "radar", "radarStyle": "standard", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#4472C4", marker={"style": "none", "size": 5})]}, title="Standard Radar")),
        case("marker-radar", rows, chart("MarkerRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#ED7D31", marker={"style": "circle", "size": 6})]}, title="Marker Radar")),
        case("filled-radar", rows, chart("FilledRadar", {"type": "radar", "radarStyle": "filled", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), fillColor="#70AD47", lineColor="#548235")]}, title="Filled Radar")),
        case("two-series", rows, chart("TwoSeriesRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#4472C4", marker={"style": "circle", "size": 6}), series("Sheet1!C1", row_range(6), row_range(6, "C"), lineColor="#ED7D31", marker={"style": "square", "size": 6})]}, title="Two Series Radar")),
        case("negative-values", [["Metric", "Score"], ["A", -4], ["B", 0], ["C", 8], ["D", -2], ["E", 13]], chart("NegativeRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#7030A0", marker={"style": "circle", "size": 6})]}, title="Negative Radar")),
        case("all-zero", [["Metric", "Score"], ["A", 0], ["B", 0], ["C", 0], ["D", 0], ["E", 0]], chart("ZeroRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#4472C4", marker={"style": "circle", "size": 6})]}, title="Zero Radar")),
        case("blank-values", [["Metric", "Score"], ["A", 4], ["B", None], ["C", "n/a"], ["D", 2], ["E", 13]], chart("BlankRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#ED7D31", marker={"style": "circle", "size": 6})]}, title="Blank Radar")),
        case("single-point", [["Metric", "Score"], ["Only", 42]], chart("SingleRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", "Sheet1!A2:A2", "Sheet1!B2:B2", lineColor="#5B9BD5", marker={"style": "circle", "size": 6})]}, title="Single Radar")),
        case("many-categories", many_rows(8), chart("ManyRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(9), row_range(9, "B"), lineColor="#A5A5A5", marker={"style": "circle", "size": 6})]}, title="Many Radar")),
        case("legend-bottom", rows, chart("BottomLegendRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#4472C4", marker={"style": "circle", "size": 6})]}, title="Bottom Legend Radar", legend="bottom")),
        case("small-position", rows, chart("SmallRadar", {"type": "radar", "radarStyle": "marker", "series": [series("Sheet1!B1", row_range(6), row_range(6, "B"), lineColor="#4472C4", marker={"style": "circle", "size": 6})]}, title="Small Radar", position=SMALL_POS)),
    ]


def surface_cases() -> list[dict[str, Any]]:
    def sg(variant: str, rows_count: int, cols_count: int) -> dict[str, Any]:
        return {"type": "surface", "surfaceVariant": variant, "series": [{"values": f"Sheet1!A{i}:{chr(ord('A') + cols_count - 1)}{i}"} for i in range(1, rows_count + 1)]}

    return [
        case("basic-top-view", [[1, 2, 3, 4], [3, 6, 2, 5], [4, 1, 7, 2]], chart("BasicSurface", sg("topView", 3, 4), title="Basic Surface")),
        case("wireframe", [[1, 2, 3, 4], [3, 6, 2, 5], [4, 1, 7, 2]], chart("WireSurface", sg("topViewWireframe", 3, 4), title="Wire Surface")),
        case("single-row", [[1, 2, 3, 4]], chart("SingleRowSurface", sg("topView", 1, 4), title="Single Row Surface")),
        case("negative-grid", [[-4, 0, 8, -2], [3, -6, 2, 5], [4, 1, -7, 2]], chart("NegativeSurface", sg("topView", 3, 4), title="Negative Surface")),
        case("blank-grid", [[1, 2, None, 4], [3, "n/a", 2, 5], [4, 1, 7, 2]], chart("BlankSurface", sg("topView", 3, 4), title="Blank Surface")),
        case("flat-grid", [[5, 5, 5], [5, 5, 5], [5, 5, 5]], chart("FlatSurface", sg("topView", 3, 3), title="Flat Surface")),
        case("larger-grid", [[1, 3, 5, 7, 9], [2, 6, 4, 8, 10], [3, 1, 9, 5, 7], [4, 8, 2, 6, 12]], chart("LargerSurface", sg("topView", 4, 5), title="Larger Surface")),
        case("small-position", [[1, 2, 3, 4], [3, 6, 2, 5], [4, 1, 7, 2]], chart("SmallSurface", sg("topView", 3, 4), title="Small Surface", position=SMALL_POS)),
        case("legend-bottom", [[1, 2, 3, 4], [3, 6, 2, 5], [4, 1, 7, 2]], chart("BottomLegendSurface", sg("topView", 3, 4), title="Bottom Legend Surface", legend="bottom")),
    ]


def stock_cases() -> list[dict[str, Any]]:
    def stock_chart(name: str, group_type: str, rows_count: int, title: str, position: dict[str, Any] = POS, legend: str = "right") -> dict[str, Any]:
        if group_type == "stockHLC":
            ser = [
                series("Sheet1!B1", row_range(rows_count), row_range(rows_count, "B"), stockRole="high"),
                series("Sheet1!C1", row_range(rows_count), row_range(rows_count, "C"), stockRole="low"),
                series("Sheet1!D1", row_range(rows_count), row_range(rows_count, "D"), stockRole="close"),
            ]
        else:
            ser = [
                series("Sheet1!B1", row_range(rows_count), row_range(rows_count, "B"), stockRole="open"),
                series("Sheet1!C1", row_range(rows_count), row_range(rows_count, "C"), stockRole="high"),
                series("Sheet1!D1", row_range(rows_count), row_range(rows_count, "D"), stockRole="low"),
                series("Sheet1!E1", row_range(rows_count), row_range(rows_count, "E"), stockRole="close"),
            ]
        return chart(name, {"type": group_type, "series": ser}, title=title, category_title="Day", value_title="Price", position=position, legend=legend)

    hlc = [["Day", "High", "Low", "Close"], ["D1", 10, 5, 8], ["D2", 12, 7, 9], ["D3", 9, 3, 4], ["D4", 14, 8, 13]]
    ohlc = [["Day", "Open", "High", "Low", "Close"], ["D1", 6, 10, 5, 8], ["D2", 8, 12, 7, 9], ["D3", 7, 9, 3, 4], ["D4", 9, 14, 8, 13]]
    return [
        case("hlc-basic", hlc, stock_chart("HlcStock", "stockHLC", 5, "HLC Stock")),
        case("ohlc-basic", ohlc, stock_chart("OhlcStock", "stockOHLC", 5, "OHLC Stock")),
        case("hlc-downtrend", [["Day", "High", "Low", "Close"], ["D1", 20, 12, 18], ["D2", 18, 10, 13], ["D3", 15, 8, 9], ["D4", 11, 4, 5]], stock_chart("DownHlcStock", "stockHLC", 5, "Downtrend Stock")),
        case("ohlc-mixed", [["Day", "Open", "High", "Low", "Close"], ["D1", 8, 10, 5, 6], ["D2", 7, 12, 6, 11], ["D3", 11, 13, 3, 4], ["D4", 5, 14, 4, 13]], stock_chart("MixedOhlcStock", "stockOHLC", 5, "Mixed OHLC")),
        case("date-categories-hlc", [["Day", "High", "Low", "Close"], [44562, 10, 5, 8], [44563, 12, 7, 9], [44565, 9, 3, 4], [44568, 14, 8, 13]], stock_chart("DateHlcStock", "stockHLC", 5, "Date HLC")),
        case("flat-range-ohlc", [["Day", "Open", "High", "Low", "Close"], ["D1", 8, 8, 8, 8], ["D2", 8, 8, 8, 8], ["D3", 8, 8, 8, 8], ["D4", 8, 8, 8, 8]], stock_chart("FlatOhlcStock", "stockOHLC", 5, "Flat OHLC")),
        case("single-point-hlc", [["Day", "High", "Low", "Close"], ["D1", 10, 5, 8]], stock_chart("SingleHlcStock", "stockHLC", 2, "Single HLC")),
        case("many-points-ohlc", [["Day", "Open", "High", "Low", "Close"], ["D1", 6, 10, 5, 8], ["D2", 8, 12, 7, 9], ["D3", 7, 9, 3, 4], ["D4", 9, 14, 8, 13], ["D5", 13, 15, 11, 12], ["D6", 12, 18, 10, 17]], stock_chart("ManyOhlcStock", "stockOHLC", 7, "Many OHLC")),
        case("small-position", hlc, stock_chart("SmallHlcStock", "stockHLC", 5, "Small HLC", position=SMALL_POS)),
        case("legend-bottom", ohlc, stock_chart("BottomLegendOhlcStock", "stockOHLC", 5, "Bottom Legend OHLC", legend="bottom")),
    ]


def funnel_cases() -> list[dict[str, Any]]:
    def fg(rows_count: int) -> dict[str, Any]:
        return {"type": "funnel", "series": [series("Sheet1!B1", row_range(rows_count), row_range(rows_count, "B"))]}

    rows = [["Stage", "Count"], ["Lead", 120], ["Qualified", 80], ["Proposal", 45], ["Closed", 20]]
    return [
        case("basic-funnel", rows, chart("BasicFunnel", fg(5), title="Basic Funnel", axes=False)),
        case("non-monotonic", [["Stage", "Count"], ["A", 40], ["B", 80], ["C", 45], ["D", 20]], chart("NonMonotonicFunnel", fg(5), title="Non Monotonic Funnel", axes=False)),
        case("single-stage", [["Stage", "Count"], ["Only", 42]], chart("SingleFunnel", fg(2), title="Single Funnel", axes=False)),
        case("many-stages", many_rows(8), chart("ManyFunnel", fg(9), title="Many Funnel", axes=False)),
        case("zero-stage", [["Stage", "Count"], ["A", 40], ["B", 0], ["C", 45], ["D", 20]], chart("ZeroFunnel", fg(5), title="Zero Funnel", axes=False)),
        case("negative-stage", [["Stage", "Count"], ["A", 40], ["B", -10], ["C", 45], ["D", 20]], chart("NegativeFunnel", fg(5), title="Negative Funnel", axes=False)),
        case("tiny-values", [["Stage", "Count"], ["A", 0.4], ["B", 0.08], ["C", 0.045], ["D", 0.02]], chart("TinyFunnel", fg(5), title="Tiny Funnel", axes=False)),
        case("blank-text-stage", [["Stage", "Count"], ["A", 40], ["B", None], ["C", "n/a"], ["D", 20]], chart("BlankTextFunnel", fg(5), title="Blank Text Funnel", axes=False)),
        case("legend-bottom", rows, chart("BottomLegendFunnel", fg(5), title="Bottom Legend Funnel", legend="bottom", axes=False)),
        case("small-position", rows, chart("SmallFunnel", fg(5), title="Small Funnel", position=SMALL_POS, axes=False)),
        case("wide-offset-position", rows, chart("WideFunnel", fg(5), title="Wide Funnel", position=WIDE_POS, axes=False)),
    ]


def waterfall_cases() -> list[dict[str, Any]]:
    def wg(rows_count: int, totals: list[int] | None = None, connectors: bool = True) -> dict[str, Any]:
        return {"type": "waterfall", "series": [series("Sheet1!B1", row_range(rows_count), row_range(rows_count, "B"), totalIndexes=totals or [], showConnectorLines=connectors)]}

    rows = [["Step", "Amount"], ["Start", 100], ["Cost", -30], ["Growth", 50], ["End", 120]]
    return [
        case("basic-waterfall", rows, chart("BasicWaterfall", wg(5, [0, 3]), title="Basic Waterfall")),
        case("no-connectors", rows, chart("NoConnectorWaterfall", wg(5, [0, 3], False), title="No Connectors Waterfall")),
        case("all-deltas", [["Step", "Amount"], ["A", 10], ["B", -3], ["C", 5], ["D", -2]], chart("DeltaWaterfall", wg(5, []), title="Delta Waterfall")),
        case("middle-subtotal", [["Step", "Amount"], ["Start", 100], ["Cost", -30], ["Subtotal", 70], ["Growth", 50], ["End", 120]], chart("MiddleSubtotalWaterfall", wg(6, [0, 2, 4]), title="Middle Subtotal Waterfall")),
        case("zero-step", [["Step", "Amount"], ["Start", 100], ["No Change", 0], ["Growth", 50], ["End", 150]], chart("ZeroStepWaterfall", wg(5, [0, 3]), title="Zero Step Waterfall")),
        case("all-negative", [["Step", "Amount"], ["Start", -10], ["Cost", -30], ["Loss", -50], ["End", -90]], chart("AllNegativeWaterfall", wg(5, [0, 3]), title="All Negative Waterfall")),
        case("single-point", [["Step", "Amount"], ["Only", 42]], chart("SingleWaterfall", wg(2, [0]), title="Single Waterfall")),
        case("many-steps", [["Step", "Amount"], ["S1", 100], ["S2", -20], ["S3", 35], ["S4", -15], ["S5", 40], ["S6", -25], ["S7", 115]], chart("ManyWaterfall", wg(8, [0, 6]), title="Many Waterfall")),
        case("large-values", [["Step", "Amount"], ["Start", 1200000], ["Cost", -350000], ["Growth", 900000], ["End", 1750000]], chart("LargeWaterfall", wg(5, [0, 3]), title="Large Waterfall")),
        case("small-position", rows, chart("SmallWaterfall", wg(5, [0, 3]), title="Small Waterfall", position=SMALL_POS)),
        case("legend-bottom", rows, chart("BottomLegendWaterfall", wg(5, [0, 3]), title="Bottom Legend Waterfall", legend="bottom")),
        case("custom-fill", rows, chart("CustomWaterfall", {"type": "waterfall", "series": [series("Sheet1!B1", row_range(5), row_range(5, "B"), fillColor="#7030A0", totalIndexes=[0, 3], showConnectorLines=True)]}, title="Custom Waterfall")),
    ]


def histogram_cases(kind: str) -> list[dict[str, Any]]:
    title_kind = "Pareto" if kind == "pareto" else "Histogram"
    def hg(rows_count: int, options: dict[str, Any]) -> dict[str, Any]:
        return {"type": kind, "series": [{"name": {"ref": "Sheet1!B1"}, "values": row_range(rows_count, "B"), "binOptions": options}]}

    rows = [["Sample", "Value"], ["A", 1], ["B", 2], ["C", 2], ["D", 4], ["E", 8], ["F", 9], ["G", 11], ["H", 12]]
    return [
        case("bin-count", rows, chart(f"BinCount{title_kind}", hg(9, {"type": "binCount", "count": 4}), title=f"Bin Count {title_kind}")),
        case("bin-width", rows, chart(f"BinWidth{title_kind}", hg(9, {"type": "binWidth", "width": 3}), title=f"Bin Width {title_kind}")),
        case("auto-bins", rows, chart(f"Auto{title_kind}", hg(9, {"type": "auto"}), title=f"Auto {title_kind}")),
        case("under-overflow", rows, chart(f"UnderOverflow{title_kind}", hg(9, {"type": "binWidth", "width": 3, "allowUnderflow": True, "underflowValue": 2, "allowOverflow": True, "overflowValue": 10}), title=f"Under Overflow {title_kind}")),
        case("underflow-only", rows, chart(f"Underflow{title_kind}", hg(9, {"type": "binWidth", "width": 3, "allowUnderflow": True, "underflowValue": 2, "allowOverflow": False}), title=f"Underflow {title_kind}")),
        case("overflow-only", rows, chart(f"Overflow{title_kind}", hg(9, {"type": "binWidth", "width": 3, "allowUnderflow": False, "allowOverflow": True, "overflowValue": 10}), title=f"Overflow {title_kind}")),
        case("negative-values", [["Sample", "Value"], ["A", -5], ["B", -2], ["C", 0], ["D", 4], ["E", 8], ["F", 9]], chart(f"Negative{title_kind}", hg(7, {"type": "binCount", "count": 4}), title=f"Negative {title_kind}")),
        case("decimal-boundaries", [["Sample", "Value"], ["A", 0.99], ["B", 1.0], ["C", 1.01], ["D", 2.99], ["E", 3.0], ["F", 3.01], ["G", 4.5]], chart(f"Decimal{title_kind}", hg(8, {"type": "binWidth", "width": 1}), title=f"Decimal {title_kind}")),
        case("blank-text-values", [["Sample", "Value"], ["A", 1], ["B", None], ["C", "n/a"], ["D", 4], ["E", 8], ["F", 9]], chart(f"BlankText{title_kind}", hg(7, {"type": "binCount", "count": 4}), title=f"Blank Text {title_kind}")),
        case("larger-sample", [["Sample", "Value"], *[[f"S{i}", (i * 7) % 23 + (i % 3) * 0.25] for i in range(1, 25)]], chart(f"LargeSample{title_kind}", hg(25, {"type": "binCount", "count": 6}), title=f"Large Sample {title_kind}")),
        case("single-value", [["Sample", "Value"], ["A", 42]], chart(f"Single{title_kind}", hg(2, {"type": "binCount", "count": 3}), title=f"Single {title_kind}")),
        case("repeated-values", [["Sample", "Value"], ["A", 5], ["B", 5], ["C", 5], ["D", 5], ["E", 5]], chart(f"Repeated{title_kind}", hg(6, {"type": "binCount", "count": 3}), title=f"Repeated {title_kind}")),
        case("small-position", rows, chart(f"Small{title_kind}", hg(9, {"type": "binCount", "count": 4}), title=f"Small {title_kind}", position=SMALL_POS)),
    ]


def box_whisker_cases() -> list[dict[str, Any]]:
    def bw(rows_count: int, **opts: Any) -> dict[str, Any]:
        defaults = {"quartileCalculation": "exclusive", "showMeanMarker": True, "showMeanLine": False, "showInnerPoints": True, "showOutlierPoints": True}
        defaults.update(opts)
        return {"type": "boxWhisker", "series": [{"name": {"ref": "Sheet1!B1"}, "values": row_range(rows_count, "B"), **defaults}]}

    rows = [["Sample", "Value"], ["A", 1], ["B", 2], ["C", 3], ["D", 4], ["E", 8], ["F", 9], ["G", 20]]
    return [
        case("exclusive-basic", rows, chart("ExclusiveBox", bw(8, quartileCalculation="exclusive"), title="Exclusive Box")),
        case("inclusive-basic", rows, chart("InclusiveBox", bw(8, quartileCalculation="inclusive"), title="Inclusive Box")),
        case("no-inner-points", rows, chart("NoInnerBox", bw(8, showInnerPoints=False), title="No Inner Points")),
        case("mean-line", rows, chart("MeanLineBox", bw(8, showMeanLine=True), title="Mean Line Box")),
        case("no-mean-marker", rows, chart("NoMeanMarkerBox", bw(8, showMeanMarker=False), title="No Mean Marker Box")),
        case("no-outliers", rows, chart("NoOutlierBox", bw(8, showOutlierPoints=False), title="No Outliers")),
        case("multi-series", [["Sample", "A", "B"], ["S1", 1, 7], ["S2", 2, 8], ["S3", 3, 9], ["S4", 4, 10], ["S5", 8, 12], ["S6", 9, 13], ["S7", 20, 30]], chart("MultiBox", {"type": "boxWhisker", "series": [{"name": {"ref": "Sheet1!B1"}, "values": "Sheet1!B2:B8", "quartileCalculation": "exclusive", "showMeanMarker": True, "showMeanLine": False, "showInnerPoints": True, "showOutlierPoints": True}, {"name": {"ref": "Sheet1!C1"}, "values": "Sheet1!C2:C8", "quartileCalculation": "exclusive", "showMeanMarker": True, "showMeanLine": False, "showInnerPoints": True, "showOutlierPoints": True}]}, title="Multi Series Box")),
        case("outlier-heavy", [["Sample", "Value"], ["A", 1], ["B", 2], ["C", 2], ["D", 3], ["E", 3], ["F", 100], ["G", -40], ["H", 4], ["I", 5]], chart("OutlierHeavyBox", bw(10), title="Outlier Heavy Box")),
        case("blank-text-values", [["Sample", "Value"], ["A", 1], ["B", None], ["C", "n/a"], ["D", 4], ["E", 8], ["F", 9]], chart("BlankTextBox", bw(7), title="Blank Text Box")),
        case("negative-values", [["Sample", "Value"], ["A", -5], ["B", -2], ["C", 0], ["D", 4], ["E", 8], ["F", 9]], chart("NegativeBox", bw(7), title="Negative Box")),
        case("single-value", [["Sample", "Value"], ["A", 42]], chart("SingleBox", bw(2), title="Single Box")),
        case("repeated-values", [["Sample", "Value"], ["A", 5], ["B", 5], ["C", 5], ["D", 5], ["E", 5]], chart("RepeatedBox", bw(6), title="Repeated Box")),
        case("small-position", rows, chart("SmallBox", bw(8), title="Small Box", position=SMALL_POS)),
    ]


TASKS = {
    "chart-column": ("column", "column", column_cases),
    "chart-bar": ("bar", "bar", bar_cases),
    "chart-line": ("line", "line", line_cases),
    "chart-area": ("area", "area", area_cases),
    "chart-pie": ("pie", "pie", lambda: pie_like_cases("pie")),
    "chart-doughnut": ("doughnut", "doughnut", lambda: pie_like_cases("doughnut")),
    "chart-scatter": ("scatter", "scatter", scatter_cases),
    "chart-bubble": ("bubble", "bubble", bubble_cases),
    "chart-radar": ("radar", "radar", radar_cases),
    "chart-surface": ("surface", "surface", surface_cases),
    "chart-stock": ("stock", "stock", stock_cases),
    "chart-funnel": ("funnel", "funnel", funnel_cases),
    "chart-waterfall": ("waterfall", "waterfall", waterfall_cases),
    "chart-histogram": ("histogram", "histogram", lambda: histogram_cases("histogram")),
    "chart-pareto": ("pareto", "pareto", lambda: histogram_cases("pareto")),
    "chart-box-whisker": ("box and whisker", "boxWhisker", box_whisker_cases),
}

VALIDATOR = '''from __future__ import annotations

from typing import Any


TASK_FAMILY = "chart-rendering"
CHART_TYPE = {chart_type!r}
ACCURACY_THRESHOLD = 0.99


def _require_ref(series: dict[str, Any], key: str) -> None:
    if not isinstance(series.get(key), str) or not series.get(key):
        raise ValueError(f"series_must_have_{{key}}")


def validate_case(case: Any) -> None:
    if not isinstance(case, dict):
        raise ValueError("case_must_be_object")
    sheets = case.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise ValueError("sheets_must_be_non_empty_list")
    chart = case.get("chart")
    if not isinstance(chart, dict):
        raise ValueError("chart_must_be_object")
    groups = chart.get("groups")
    if not isinstance(groups, list) or len(groups) != 1:
        raise ValueError("chart_must_have_one_group")
    group = groups[0]
    if not isinstance(group, dict):
        raise ValueError("chart_group_must_be_object")
    group_type = group.get("type")
    if CHART_TYPE == "stock":
        if group_type not in ("stockHLC", "stockOHLC"):
            raise ValueError("chart_group_must_be_stock")
    elif group_type != CHART_TYPE:
        raise ValueError(f"chart_group_must_be_{{CHART_TYPE}}")
    series = group.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("chart_must_have_series")
    for item in series:
        if not isinstance(item, dict):
            raise ValueError("series_must_be_object")
        if CHART_TYPE in ("scatter", "bubble"):
            _require_ref(item, "xValues")
            _require_ref(item, "yValues")
            if CHART_TYPE == "bubble":
                _require_ref(item, "bubbleSizes")
        elif CHART_TYPE == "surface":
            _require_ref(item, "values")
        elif CHART_TYPE in ("histogram", "pareto", "boxWhisker"):
            _require_ref(item, "values")
        elif CHART_TYPE == "stock":
            _require_ref(item, "categories")
            _require_ref(item, "values")
            if item.get("stockRole") not in ("open", "high", "low", "close", "volume"):
                raise ValueError("stock_series_must_have_stockRole")
        else:
            _require_ref(item, "categories")
            _require_ref(item, "values")
'''


def instruction(task_label: str, cases: list[dict[str, Any]]) -> str:
    example = json.dumps(strip_case_id(cases[0]), separators=(",", ":"))
    return f"""You need to implement a renderer for a small Excel-compatible {task_label} chart subset.

Each input line is a JSON object with:

- `sheets`: workbook sheet data
- `chart`: a JSON chart specification

The oracle returns the reference PNG rendering for that chart and sheet data. All renders use PNG output at dpr 1 and zoom 1.

Query the oracle with:

```bash
oracle-query < inputs.jsonl
```

Each oracle output line is JSON:

```json
{{"contentType":"image/png","pixelWidth":318,"pixelHeight":210,"data":"...base64 png bytes..."}}
```

Protocol errors, such as exceeding the query budget, are not part of the chart behavior.

Create an executable at:

```bash
/app/solution/solve
```

It must read JSONL inputs from stdin and write one JSONL output per input to stdout using the same output format as the oracle. The output must always be PNG at dpr 1 and zoom 1.

You may implement the renderer in any language. Python, Node, npm, and uv are available. If your solution needs third-party dependencies at grading time, put a `package.json` or `pyproject.toml` inside `/app/solution`; the grader will install those dependencies before running `/app/solution/solve`.

When finished, package your solution for grading:

```bash
mkdir -p /logs/artifacts
tar -czf /logs/artifacts/submission.tgz -C /app solution
```

The grader will run your submitted CLI on fixed hidden evaluation inputs and compare the rendered PNGs against its own trusted oracle using full-image MS-SSIM. The rollout oracle service will not be reachable during grading.

Example input:

```json
{example}
```
"""


def task_toml(slug: str, task_label: str, chart_type: str) -> str:
    return f'''schema_version = "1.3"
artifacts = []

[task]
name = "mimic-bench/{slug}"
description = "Implement a PNG renderer for a small Excel-compatible {task_label} chart subset using a queryable chart-preview oracle."
authors = [{{ name = "Nuno" }}]
keywords = ["oracle", "chart-rendering", "jsonl", "coding-agents"]

[metadata]
difficulty = "medium"
category = "programming"
tags = ["oracle", "black-box", "chart-rendering", "excel-compatible"]
family = "chart-rendering"
chart_type = "{chart_type}"

[agent]
timeout_sec = 5400.0
user = "agent"

[verifier]
timeout_sec = 300.0
environment_mode = "separate"
network_mode = "public"

[verifier.env]
WITAN_API_URL = "${{WITAN_API_URL}}"
WITAN_API_KEY = "${{WITAN_API_KEY}}"
QUERY_BUDGET = "${{QUERY_BUDGET}}"

[verifier.environment]
network_mode = "public"
cpus = 1
memory_mb = 2048
storage_mb = 4096

[environment]
build_timeout_sec = 600.0
network_mode = "public"
cpus = 1
memory_mb = 2048
storage_mb = 4096
gpus = 0

[environment.env]
QUERY_BUDGET = "${{QUERY_BUDGET}}"
'''


def write_task(slug: str, task_label: str, chart_type: str, make_cases) -> None:
    destination = TASKS_DIR / slug
    if not destination.exists():
        shutil.copytree(SOURCE_TASK, destination)
    cases = normalize_cases(slug, make_cases())
    public_cases = [strip_case_id(item) for item in cases]
    (destination / "instruction.md").write_text(instruction(task_label, cases))
    (destination / "task.toml").write_text(task_toml(slug, task_label, chart_type))
    (destination / "tests" / "oracle_task.py").write_text(VALIDATOR.format(chart_type=chart_type))
    (destination / "tests" / "eval_inputs.jsonl").write_text(
        "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in public_cases)
    )
    print(f"{slug}: {len(cases)} cases")


def main() -> None:
    for slug, (task_label, chart_type, make_cases) in TASKS.items():
        write_task(slug, task_label, chart_type, make_cases)


if __name__ == "__main__":
    main()
