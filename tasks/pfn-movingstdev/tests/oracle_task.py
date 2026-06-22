from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'MOVINGSTDEV'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(values,window,[sample],\n  LET(x,TOROW(values), n,COLUMNS(x), w,window, s,IF(ISOMITTED(sample),TRUE,sample),\n    MAKEARRAY(1,n,LAMBDA(r,c,IF(c<w,"",ROUND(IF(s,STDEV.S(MAKEARRAY(w,1,LAMBDA(i,j,INDEX(x,1,c-w+i)))),STDEV.P(MAKEARRAY(w,1,LAMBDA(i,j,INDEX(x,1,c-w+i))))),6))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
