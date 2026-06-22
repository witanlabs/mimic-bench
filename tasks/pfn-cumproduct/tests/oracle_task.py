from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'CUMPRODUCT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(array,[axis],\n  LET(a,array, ax,IF(ISOMITTED(axis),"rows",LOWER(axis)),\n    MAKEARRAY(ROWS(a),COLUMNS(a),LAMBDA(r,c,IF(ax="cols",PRODUCT(MAKEARRAY(1,c,LAMBDA(i,j,INDEX(a,r,j)))),PRODUCT(MAKEARRAY(r,1,LAMBDA(i,j,INDEX(a,i,c)))))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
