from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DATEADD'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3,)
LAMBDA_BODY = 'LAMBDA(date,amount,unit,\n  LET(u,LOWER(unit),SWITCH(u,\n    "year",EDATE(date,amount*12),"years",EDATE(date,amount*12),"y",EDATE(date,amount*12),\n    "quarter",EDATE(date,amount*3),"quarters",EDATE(date,amount*3),"q",EDATE(date,amount*3),\n    "month",EDATE(date,amount),"months",EDATE(date,amount),"m",EDATE(date,amount),\n    "week",date+amount*7,"weeks",date+amount*7,"w",date+amount*7,\n    "day",date+amount,"days",date+amount,"d",date+amount,\n    "hour",date+amount/24,"hours",date+amount/24,"h",date+amount/24,\n    "minute",date+amount/1440,"minutes",date+amount/1440,"n",date+amount/1440,\n    "second",date+amount/86400,"seconds",date+amount/86400,"s",date+amount/86400)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
