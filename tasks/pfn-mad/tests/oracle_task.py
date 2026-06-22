from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'MAD'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(values,[center],[scale],\n  LET(x,TOCOL(values,1), c,IF(ISOMITTED(center),MEDIAN(x),center), s,IF(ISOMITTED(scale),1,scale), MEDIAN(ABS(x-c))*s))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
