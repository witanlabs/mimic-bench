from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'LINEARINTERP'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3, 4)
LAMBDA_BODY = 'LAMBDA(x,known_x,known_y,[extrapolate],\n  LET(kx,TOCOL(known_x), ky,TOCOL(known_y), n,ROWS(TOCOL(known_x)),\n    p,IFERROR(MAX(FILTER(SEQUENCE(n-1),MAKEARRAY(n-1,1,LAMBDA(i,j,AND(INDEX(kx,i)<=x,x<=INDEX(kx,i+1)))))),0),\n    IF(p=0,NA(),LET(xLo,INDEX(kx,p),xHi,INDEX(kx,p+1),yLo,INDEX(ky,p),yHi,INDEX(ky,p+1),ROUND(yLo+(x-xLo)*(yHi-yLo)/(xHi-xLo),6)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
