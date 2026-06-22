from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'POLYVAL'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2,)
LAMBDA_BODY = 'LAMBDA(coefficients,x,\n  LET(c,TOROW(coefficients), xs,TOROW(x), n,COLUMNS(c),\n    MAP(xs,LAMBDA(z,ROUND(SUM(MAP(c,SEQUENCE(1,n,n-1,-1),LAMBDA(coef,ex,coef*IF(ex=0,1,z^ex)))),6)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
