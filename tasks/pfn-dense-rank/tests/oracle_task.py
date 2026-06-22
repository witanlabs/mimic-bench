from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DENSE_RANK'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(values,[order],\n  LET(x,TOCOL(values), ord,IF(ISOMITTED(order),1,order), u,SORT(UNIQUE(x),,ord), TOROW(MAP(x,LAMBDA(v,XMATCH(v,u))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
