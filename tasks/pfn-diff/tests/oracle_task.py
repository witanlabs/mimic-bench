from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DIFF'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3, 4)
LAMBDA_BODY = 'LAMBDA(array,[lag],[axis],[fill],\n  LET(a,array, k,IF(ISOMITTED(lag),1,lag), ax,IF(ISOMITTED(axis),"rows",LOWER(axis)), f,IF(ISOMITTED(fill),"",fill),\n    MAKEARRAY(ROWS(a),COLUMNS(a),LAMBDA(r,c,LET(rr,IF(ax="cols",r,r-k), cc,IF(ax="cols",c-k,c),\n      IF(OR(rr<1,cc<1),f,INDEX(a,r,c)-INDEX(a,rr,cc)))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
