from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'IMTOPOLAR'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(inumber,[part],\n  LET(x,IMREAL(inumber), y,IMAGINARY(inumber), p,IF(ISOMITTED(part),"all",LOWER(part)),\n    SWITCH(p,"radius",SQRT(x^2+y^2),"theta",ATAN2(x,y),HSTACK(SQRT(x^2+y^2),ATAN2(x,y)))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
