from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DATEBUCKET'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3, 4)
LAMBDA_BODY = 'LAMBDA(date,interval,unit,[origin],\n  LET(o,IF(ISOMITTED(origin),DATE(1900,1,1),origin), u,LOWER(unit),\n    SWITCH(u,"month",EDATE(o,interval*QUOTIENT(DATEDIF(o,date,"m"),interval)),\n      "day",o+interval*QUOTIENT(date-o,interval),\n      "hour",o+(interval/24)*QUOTIENT((date-o)*24,interval),\n      "minute",o+(interval/1440)*QUOTIENT((date-o)*1440,interval),\n      "second",o+(interval/86400)*QUOTIENT((date-o)*86400,interval))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
