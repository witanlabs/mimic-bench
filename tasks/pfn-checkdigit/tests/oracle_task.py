from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'CHECKDIGIT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2,)
LAMBDA_BODY = 'LAMBDA(value,method,\n  LET(s,TEXT(value,"@"), m,LOWER(method), n,LEN(s),\n    SWITCH(m,\n      "luhn",LET(total,SUM(MAP(SEQUENCE(n),LAMBDA(i,LET(d,--MID(s,n-i+1,1), e,IF(ISODD(i),d*2,d), IF(e>9,e-9,e))))),MOD(10-MOD(total,10),10)),\n      "isbn13",LET(total,SUM(MAP(SEQUENCE(12),LAMBDA(i,--MID(s,i,1)*IF(ISODD(i),1,3)))),MOD(10-MOD(total,10),10)),\n      VALUE(""))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
