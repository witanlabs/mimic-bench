from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'FUZZYMATCH'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(text,candidates,[threshold],\n  LET(t,IF(ISOMITTED(threshold),2,threshold), c,TOCOL(candidates,1),\n    scores,MAP(c,LAMBDA(x,EDITDISTANCE(LOWER(text),LOWER(x)))),\n    best,XMATCH(MIN(scores),scores),\n    IF(MIN(scores)<=t,INDEX(c,best),NA())))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
