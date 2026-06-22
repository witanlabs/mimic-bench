from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DRAWDOWN'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(values,[mode],\n  LET(x,TOCOL(values), peaks,SCAN(INDEX(x,1),x,LAMBDA(p,v,MAX(p,v))), TOROW(ROUND((x-peaks)/peaks,6))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
