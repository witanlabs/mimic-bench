from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'CSVBUILD'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(array,[delimiter],[quote_mode],\n  LET(d,IF(ISOMITTED(delimiter),",",delimiter),\n    TEXTJOIN(d,,MAP(TOROW(array),LAMBDA(v,LET(s,TEXT(v,"@"),\n      IF(OR(ISNUMBER(SEARCH(d,s)),ISNUMBER(SEARCH(CHAR(34),s)),ISNUMBER(SEARCH(CHAR(10),s))),\n        CHAR(34)&SUBSTITUTE(s,CHAR(34),CHAR(34)&CHAR(34))&CHAR(34),s)))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
