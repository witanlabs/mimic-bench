from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'CORRMATRIX'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(array,[method],\n  LET(a,array, cols,COLUMNS(a), rows,ROWS(a),\n    MAKEARRAY(cols,cols,LAMBDA(i,j,ROUND(CORREL(MAKEARRAY(rows,1,LAMBDA(r,c,INDEX(a,r,i))),MAKEARRAY(rows,1,LAMBDA(r,c,INDEX(a,r,j)))),6)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
