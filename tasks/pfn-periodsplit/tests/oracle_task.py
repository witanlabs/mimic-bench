from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'PERIODSPLIT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(start,end,[unit],\n  LET(s0,DATEVALUE(start), e,DATEVALUE(end), u,IF(ISOMITTED(unit),"month",LOWER(unit)),\n    s,IF(u="quarter",DATE(YEAR(s0),1+3*QUOTIENT(MONTH(s0)-1,3),1),DATE(YEAR(s0),MONTH(s0),1)),\n    step,IF(u="quarter",3,1), n,QUOTIENT(DATEDIF(s,e,"m"),step)+1,\n    TOROW(MAP(SEQUENCE(n),LAMBDA(i,EDATE(s,(i-1)*step))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
