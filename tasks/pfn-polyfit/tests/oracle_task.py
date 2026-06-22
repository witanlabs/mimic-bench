from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'POLYFIT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3,)
LAMBDA_BODY = 'LAMBDA(x,y,degree,\n  LET(xv,TOCOL(x), yv,TOCOL(y), mx,AVERAGE(xv), my,AVERAGE(yv),\n    slope,SUM((xv-mx)*(yv-my))/SUM((xv-mx)^2), intercept,my-slope*mx,\n    HSTACK(ROUND(slope,6),ROUND(intercept,6))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
