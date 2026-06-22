from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'HISTOGRAM'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3, 4)
LAMBDA_BODY = 'LAMBDA(values,bins,[closed],[labels],\n  LET(v,TOCOL(values,1), b,TOCOL(bins,1), counts,FREQUENCY(v,b),\n    IF(IF(ISOMITTED(labels),FALSE,labels),\n      HSTACK(VSTACK("<="&b,">"&TAKE(b,-1)),counts),\n      TOROW(counts))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
