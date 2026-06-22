from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'ISOYEAR'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1,)
LAMBDA_BODY = 'LAMBDA(date,\n  LET(d,DATEVALUE(date), YEAR(d-WEEKDAY(d,2)+4)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
