from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'AGE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(birth_date,[as_of],[unit],\n  LET(b,DATEVALUE(birth_date), a,DATEVALUE(as_of), u,IF(ISOMITTED(unit),"ymd",LOWER(unit)),\n    SWITCH(u,"days",a-b,"months",DATEDIF(b,a,"m"),"years",DATEDIF(b,a,"y"),\n      DATEDIF(b,a,"y")&"y "&DATEDIF(b,a,"ym")&"m "&DATEDIF(b,a,"md")&"d")))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
