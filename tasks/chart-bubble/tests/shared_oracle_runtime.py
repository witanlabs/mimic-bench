from __future__ import annotations

import base64
import os
import re
import tempfile
from importlib import import_module
from pathlib import Path
from typing import Any

from PIL import Image
from witan.workbook import Workbook


RPC_TIMEOUT_SEC = float(os.environ.get("WITAN_RPC_TIMEOUT_SEC", "60"))
DEFAULT_QUERY_BUDGET = 64
DEFAULT_SHEET_NAME = "Sheet1"
DATA_URL_RE = re.compile(r"^data:(image/[a-z0-9.+-]+);base64,(.*)$", re.IGNORECASE | re.DOTALL)


def oracle_task():
    return import_module("oracle_task")


def protocol_error(code: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "protocol_error": code, **extra}


def query_budget() -> int:
    value = os.environ.get("QUERY_BUDGET", "").strip()
    return int(value) if value else DEFAULT_QUERY_BUDGET


def normalize_preview(data_url: str) -> dict[str, Any]:
    match = DATA_URL_RE.match(data_url)
    if match is None:
        return protocol_error("bad_preview_data_url")
    content_type = match.group(1).lower()
    data = match.group(2)
    image_bytes = base64.b64decode(data)
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        tmp.write(image_bytes)
        tmp.flush()
        with Image.open(tmp.name) as image:
            width, height = image.size
    return {
        "contentType": content_type,
        "pixelWidth": width,
        "pixelHeight": height,
        "data": data,
    }


def cells_for_sheet(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    name = sheet.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("sheet_missing_name")
    cells = sheet.get("cells")
    if not isinstance(cells, list):
        raise ValueError("sheet_cells_must_be_list")

    out = []
    for cell in cells:
        if not isinstance(cell, dict):
            raise ValueError("cell_must_be_object")
        address = cell.get("address")
        if not isinstance(address, str) or not address:
            raise ValueError("cell_missing_address")
        payload = {"address": address if "!" in address else f"{name}!{address}"}
        if "formula" in cell:
            payload["formula"] = cell["formula"]
        else:
            payload["value"] = cell.get("value")
        out.append(payload)
    return out


class ChartOracle:
    def __init__(self) -> None:
        api_url = os.environ.get("WITAN_API_URL", "").strip()
        api_key = os.environ.get("WITAN_API_KEY", "").strip()
        if not api_url:
            raise RuntimeError("WITAN_API_URL is not set")
        if not api_key:
            raise RuntimeError("WITAN_API_KEY is not set")
        self.api_url = api_url
        self.api_key = api_key

    def render_case(self, case: dict[str, Any]) -> dict[str, Any]:
        task = oracle_task()
        try:
            task.validate_case(case)
        except ValueError as exc:
            return protocol_error(str(exc))

        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "chart.xlsx"
            workbook = Workbook(
                workbook_path,
                create=True,
                stateless=True,
                api_url=self.api_url,
                api_key=self.api_key,
                request_timeout=RPC_TIMEOUT_SEC,
            )
            try:
                sheets = case.get("sheets")
                if not isinstance(sheets, list) or not sheets:
                    raise ValueError("sheets_must_be_non_empty_list")
                for sheet in sheets:
                    if not isinstance(sheet, dict):
                        raise ValueError("sheet_must_be_object")
                    name = sheet.get("name")
                    if not isinstance(name, str) or not name:
                        raise ValueError("sheet_missing_name")
                    workbook.add_sheet(name)
                cells = [cell for sheet in sheets for cell in cells_for_sheet(sheet)]
                if cells:
                    workbook.set_cells(cells)

                sheet_name = str(case.get("chartSheet") or sheets[0].get("name") or DEFAULT_SHEET_NAME)
                added = workbook.add_chart(sheet_name, case["chart"])
                selector = added.get("id") or added.get("name") or case["chart"].get("name")
                preview = workbook.preview_chart(sheet_name, selector, format="png", dpr=1, zoom=1)
                return normalize_preview(preview)
            finally:
                workbook.close()


def expected_outputs(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    oracle = ChartOracle()
    return [oracle.render_case(case) for case in cases]
