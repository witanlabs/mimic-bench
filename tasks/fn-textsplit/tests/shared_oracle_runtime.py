from __future__ import annotations

import math
import os
import tempfile
from importlib import import_module
from pathlib import Path
from typing import Any

from witan.workbook import Workbook


RPC_TIMEOUT_SEC = float(os.environ.get("WITAN_RPC_TIMEOUT_SEC", "45"))
DEFAULT_QUERY_BUDGET = 256
SHEET_NAME = os.environ.get("WITAN_ORACLE_SHEET", "Sheet1")
INPUT_COLUMNS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ERROR_FORMULAS = {
    "#N/A": "=NA()",
    "#VALUE!": '=VALUE("oracle")',
    "#DIV/0!": "=1/0",
    "#NUM!": "=SQRT(-1)",
    "#REF!": '=INDIRECT("#REF!")',
}


def oracle_task():
    return import_module("oracle_task")


def protocol_error(code: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "protocol_error": code, **extra}


def query_budget() -> int:
    value = os.environ.get("QUERY_BUDGET", "").strip()
    return int(value) if value else DEFAULT_QUERY_BUDGET


def project_formula_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return protocol_error("bad_formula_result")

    error = result.get("error")
    if error:
        if isinstance(error, dict):
            code = str(error.get("code") or error.get("message") or "#VALUE!")
        else:
            code = str(error)
        return {"value": None, "error": code}

    return {"value": result.get("value"), "error": None}


def task_arity(task: Any) -> int:
    arity = int(getattr(task, "ARITY"))
    if arity < 1 or arity > len(INPUT_COLUMNS):
        raise RuntimeError("unsupported task arity")
    return arity


def cell_payload(address: str, value: Any) -> dict[str, Any]:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return {"address": address, "value": value}

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("non_finite_number")
        return {"address": address, "value": value}

    if isinstance(value, dict) and value.get("type") == "error":
        code = str(value.get("value", "")).strip().upper()
        formula = ERROR_FORMULAS.get(code)
        if formula is None:
            raise ValueError("unsupported_error_code")
        return {"address": address, "formula": formula}

    raise ValueError("unsupported_argument")


def cells_for_args(args: Any, row: int, arity: int) -> list[dict[str, Any]]:
    if not isinstance(args, list) or len(args) != arity:
        raise ValueError("bad_arity")

    cells = []
    for index, value in enumerate(args):
        cells.append(cell_payload(f"{SHEET_NAME}!{INPUT_COLUMNS[index]}{row}", value))
    return cells


def task_arg_mode(task: Any) -> str:
    return str(getattr(task, "ARG_MODE", "cell_values"))


class WitanFormulaOracle:
    def __init__(self) -> None:
        api_url = os.environ.get("WITAN_API_URL", "").strip()
        api_key = os.environ.get("WITAN_API_KEY", "").strip()
        if not api_url:
            raise RuntimeError("WITAN_API_URL is not set")
        if not api_key:
            raise RuntimeError("WITAN_API_KEY is not set")

        self.temp_dir = tempfile.TemporaryDirectory()
        workbook_path = Path(self.temp_dir.name) / "oracle.xlsx"
        self.workbook = Workbook(
            workbook_path,
            create=True,
            stateless=True,
            api_url=api_url,
            api_key=api_key,
            request_timeout=RPC_TIMEOUT_SEC,
        )
        self.workbook.add_sheet(SHEET_NAME)
        self.next_row = 1

    def close(self) -> None:
        self.workbook.close()
        self.temp_dir.cleanup()

    def evaluate_args(self, args: Any) -> dict[str, Any]:
        task = oracle_task()
        if task_arg_mode(task) == "formula_literals":
            try:
                formula = task.formula_for_args(args)
            except ValueError as exc:
                return protocol_error(str(exc))
            return self.evaluate_formulas([formula])[0]

        arity = task_arity(task)
        row = self.next_row
        self.next_row += 1
        try:
            cells = cells_for_args(args, row, arity)
        except ValueError as exc:
            return protocol_error(str(exc))
        self.workbook.set_cells(cells)
        formula = task.formula_for_row(row)
        return self.evaluate_formulas([formula])[0]

    def evaluate_cases(self, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        task = oracle_task()
        if task_arg_mode(task) == "formula_literals":
            formulas = [task.formula_for_args(case.get("args")) for case in cases]
            return self.evaluate_formulas(formulas)

        arity = task_arity(task)
        cells = []
        formulas = []
        for row, case in enumerate(cases, start=1):
            cells.extend(cells_for_args(case.get("args"), row, arity))
            formulas.append(task.formula_for_row(row))
        self.workbook.set_cells(cells)
        return self.evaluate_formulas(formulas)

    def evaluate_formulas(self, formulas: list[str]) -> list[dict[str, Any]]:
        results = self.workbook.evaluate_formulas(SHEET_NAME, formulas)
        if not isinstance(results, list) or len(results) != len(formulas):
            raise RuntimeError("bad Witan evaluate_formulas result shape")
        return [project_formula_result(result) for result in results]


def expected_outputs(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    oracle = WitanFormulaOracle()
    try:
        return oracle.evaluate_cases(cases)
    finally:
        oracle.close()
