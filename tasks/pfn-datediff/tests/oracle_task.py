from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DATEDIFF'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3,)
LAMBDA_BODY = 'LAMBDA(start_date,end_date,unit,\n  LET(u,LOWER(unit),SWITCH(u,\n    "year",DATEDIF(start_date,end_date,"y"),"years",DATEDIF(start_date,end_date,"y"),"y",DATEDIF(start_date,end_date,"y"),\n    "month",DATEDIF(start_date,end_date,"m"),"months",DATEDIF(start_date,end_date,"m"),"m",DATEDIF(start_date,end_date,"m"),\n    "week",QUOTIENT(end_date-start_date,7),"weeks",QUOTIENT(end_date-start_date,7),"w",QUOTIENT(end_date-start_date,7),\n    "day",end_date-start_date,"days",end_date-start_date,"d",end_date-start_date,\n    "hour",QUOTIENT((end_date-start_date)*24,1),"hours",QUOTIENT((end_date-start_date)*24,1),\n    "minute",QUOTIENT((end_date-start_date)*1440,1),"minutes",QUOTIENT((end_date-start_date)*1440,1),\n    "second",QUOTIENT((end_date-start_date)*86400,1),"seconds",QUOTIENT((end_date-start_date)*86400,1))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
