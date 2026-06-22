from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'QUERYSTRINGPARSE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(query,[decode],\n  LET(q,IF(LEFT(query,1)="?",RIGHT(query,LEN(query)-1),query), parts,TEXTSPLIT(q,"&"), n,COLUMNS(parts),\n    MAKEARRAY(n,2,LAMBDA(r,c,LET(kv,TEXTSPLIT(INDEX(parts,1,r),"="), SUBSTITUTE(INDEX(kv,1,c),"+"," "))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
