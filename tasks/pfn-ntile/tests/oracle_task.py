from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'NTILE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(values,buckets,[order],\n  LET(x,TOCOL(values), n,ROWS(x), ord,IF(ISOMITTED(order),1,order), idx,SEQUENCE(n),\n    sorted,SORTBY(idx,x,ord,idx,1),\n    TOROW(MAP(idx,LAMBDA(k,QUOTIENT((XMATCH(k,sorted)-1)*buckets,n)+1)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
