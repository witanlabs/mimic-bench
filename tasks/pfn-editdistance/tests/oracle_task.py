from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'EDITDISTANCE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2,)
LAMBDA_BODY = 'LAMBDA(text1,text2,\n  LET(a,text1,b,text2, la,LEN(a), lb,LEN(b),\n    IF(la=0,lb,IF(lb=0,la,\n      MIN(EDITDISTANCE(LEFT(a,la-1),b)+1,\n          EDITDISTANCE(a,LEFT(b,lb-1))+1,\n          EDITDISTANCE(LEFT(a,la-1),LEFT(b,lb-1))+(RIGHT(a,1)<>RIGHT(b,1)))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
