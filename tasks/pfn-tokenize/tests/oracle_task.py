from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'TOKENIZE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(text,[pattern],[lowercase],\n  LET(p,IF(ISOMITTED(pattern),"[^A-Za-z0-9]+",pattern), lc,IF(ISOMITTED(lowercase),TRUE,lowercase), src,IF(lc,LOWER(text),text),\n    t,TOCOL(TEXTSPLIT(REGEXREPLACE(src,p,CHAR(29)),CHAR(29))),\n    TOROW(FILTER(t,t<>""))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
