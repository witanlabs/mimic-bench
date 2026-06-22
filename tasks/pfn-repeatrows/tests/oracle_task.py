from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'REPEATROWS'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2,)
LAMBDA_BODY = 'LAMBDA(array,counts,\n  LET(a,array, cnt,TOCOL(IF(ROWS(counts)*COLUMNS(counts)=1,SEQUENCE(ROWS(a),,counts,0),counts)),\n    cum,SCAN(0,cnt,LAMBDA(s,x,s+x)),\n    MAKEARRAY(SUM(cnt),COLUMNS(a),LAMBDA(r,c,INDEX(a,XMATCH(r,cum,1),c)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
