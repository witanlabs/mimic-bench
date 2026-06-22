from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DATETRUNC'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(date,unit,[week_start],\n  LET(u,LOWER(unit), weekStart,IF(ISOMITTED(week_start),1,week_start),\n    SWITCH(u,"year",DATE(YEAR(date),1,1),"quarter",DATE(YEAR(date),1+3*QUOTIENT(MONTH(date)-1,3),1),\n      "month",DATE(YEAR(date),MONTH(date),1),"week",INT(date)-MOD(WEEKDAY(date,2)-weekStart,7),\n      "day",INT(date),"hour",ROUND(FLOOR(date,1/24),10),"minute",ROUND(FLOOR(date,1/1440),10),"second",ROUND(FLOOR(date,1/86400),10))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
