from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'RSI'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(prices,[period],\n  LET(p,TOROW(prices), n,COLUMNS(p), per,IF(ISOMITTED(period),14,period),\n    ch,MAKEARRAY(1,n-1,LAMBDA(r,c,INDEX(p,1,c+1)-INDEX(p,1,c))),\n    MAKEARRAY(1,n,LAMBDA(r,c,IF(c<=per,"",\n      LET(win,MAKEARRAY(1,per,LAMBDA(i,j,INDEX(ch,1,c-per+j-1))),\n        gain,AVERAGE(MAP(win,LAMBDA(v,MAX(0,v)))), loss,AVERAGE(MAP(win,LAMBDA(v,MAX(0,-v)))),\n        IF(loss=0,100,ROUND(100-100/(1+gain/loss),6))))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
