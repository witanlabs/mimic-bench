from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'TEXTBETWEEN'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3, 4, 5)
LAMBDA_BODY = 'LAMBDA(text,start_text,end_text,[instance_num],[match_mode],\n  LET(n,IF(ISOMITTED(instance_num),1,instance_num), mm,IF(ISOMITTED(match_mode),0,match_mode),\n    TEXTBEFORE(TEXTAFTER(text,start_text,n,mm),end_text,1,mm)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
