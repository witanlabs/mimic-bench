from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'WINSORIZE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3, 4)
LAMBDA_BODY = 'LAMBDA(array,lower,upper,[is_percent],\n  LET(a,array, p,IF(ISOMITTED(is_percent),TRUE,is_percent), x,TOCOL(a,1),\n    lo,IF(p,PERCENTILE.INC(x,lower),lower), hi,IF(p,PERCENTILE.INC(x,upper),upper),\n    MAP(a,LAMBDA(v,MIN(MAX(v,lo),hi)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
