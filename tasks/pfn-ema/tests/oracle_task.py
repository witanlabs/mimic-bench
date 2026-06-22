from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'EMA'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(values,alpha_or_span,[mode],\n  LET(x,TOCOL(values), n,ROWS(x), a,alpha_or_span,\n    TOROW(ROUND(SCAN(INDEX(x,1),SEQUENCE(n),LAMBDA(prev,i,IF(i=1,INDEX(x,1),a*INDEX(x,i)+(1-a)*prev))),6))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
