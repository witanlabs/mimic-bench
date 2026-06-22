from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'QUANTILECUT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(values,bins,[labels],\n  LET(x,TOCOL(values), n,ROWS(x), idx,SEQUENCE(n), sorted,SORTBY(idx,x,1,idx,1),\n    TOROW(MAP(idx,LAMBDA(k,MIN(bins,QUOTIENT((XMATCH(k,sorted)-1)*bins,n)+1))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
