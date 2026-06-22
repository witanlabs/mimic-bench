from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'IBANVALIDATE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(iban,[return_type],\n  LET(s,UPPER(SUBSTITUTE(iban," ","")), moved,RIGHT(s,LEN(s)-4)&LEFT(s,4),\n    chars,MID(moved,SEQUENCE(LEN(moved)),1),\n    digits,TEXTJOIN("",,MAP(chars,LAMBDA(ch,IF(ISNUMBER(--ch),ch,CODE(ch)-55)))),\n    REDUCE(0,MID(digits,SEQUENCE(LEN(digits)),1),LAMBDA(rem,d,MOD(rem*10+--d,97)))=1))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
