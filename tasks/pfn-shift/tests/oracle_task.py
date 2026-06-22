from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'SHIFT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3, 4)
LAMBDA_BODY = 'LAMBDA(array,[row_offset],[col_offset],[fill],\n  LET(a,array, dr,IF(ISOMITTED(row_offset),0,row_offset), dc,IF(ISOMITTED(col_offset),0,col_offset), f,IF(ISOMITTED(fill),"",fill),\n    MAKEARRAY(ROWS(a),COLUMNS(a),LAMBDA(r,c,LET(sr,r-dr, sc,c-dc, IF(OR(sr<1,sc<1,sr>ROWS(a),sc>COLUMNS(a)),f,INDEX(a,sr,sc)))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
