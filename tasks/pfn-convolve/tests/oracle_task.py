from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'CONVOLVE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(array,kernel,[mode],\n  LET(x,TOCOL(array), k,TOCOL(kernel), n,ROWS(x), m,ROWS(k), md,IF(ISOMITTED(mode),"full",LOWER(mode)),\n    start,SWITCH(md,"valid",m-1,"same",QUOTIENT(m-1,2),0),\n    len,SWITCH(md,"valid",n-m+1,"same",n,n+m-1),\n    TOROW(MAKEARRAY(len,1,LAMBDA(r,c,LET(i,r+start,SUM(MAKEARRAY(m,1,LAMBDA(t,u,IF(AND(i-t+1>=1,i-t+1<=n),INDEX(x,i-t+1)*INDEX(k,t),0))))))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
