from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'ROLL'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(array,[row_offset],[col_offset],\n  LET(a,array, dr,IF(ISOMITTED(row_offset),0,row_offset), dc,IF(ISOMITTED(col_offset),0,col_offset),\n    MAKEARRAY(ROWS(a),COLUMNS(a),LAMBDA(r,c,INDEX(a,MOD(r-dr-1,ROWS(a))+1,MOD(c-dc-1,COLUMNS(a))+1)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
