from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'SLUG'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(text,[max_length],[separator],\n  LET(sep,IF(ISOMITTED(separator),"-",separator), n,IF(ISOMITTED(max_length),32767,max_length),\n    s,LOWER(STRIPDIACRITICS(text)),\n    cleaned,REGEXREPLACE(s,"[^a-z0-9]+",sep),\n    collapsed,REGEXREPLACE(cleaned,sep&"+",sep),\n    LEFT(REGEXREPLACE(collapsed,"^"&sep&"|"&sep&"$",""),n)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
