from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'REPEATCOLS'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2,)
LAMBDA_BODY = 'LAMBDA(array,counts,\n  LET(a,array, cnt,TOROW(IF(ROWS(counts)*COLUMNS(counts)=1,MAKEARRAY(1,COLUMNS(a),LAMBDA(r,c,counts)),counts)),\n    cum,SCAN(0,cnt,LAMBDA(s,x,s+x)),\n    MAKEARRAY(ROWS(a),SUM(cnt),LAMBDA(r,c,INDEX(a,r,XMATCH(c,cum,1))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
