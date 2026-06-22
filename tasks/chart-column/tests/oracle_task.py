from __future__ import annotations

from typing import Any


TASK_FAMILY = "chart-rendering"
CHART_TYPE = 'column'
ACCURACY_THRESHOLD = 0.99


def _require_ref(series: dict[str, Any], key: str) -> None:
    if not isinstance(series.get(key), str) or not series.get(key):
        raise ValueError(f"series_must_have_{key}")


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
        raise ValueError(f"chart_group_must_be_{CHART_TYPE}")
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
