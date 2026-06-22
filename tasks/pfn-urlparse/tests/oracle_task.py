from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'URLPARSE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3)
LAMBDA_BODY = 'LAMBDA(url,part,[param],\n  LET(p,LOWER(part), u,url,\n    SWITCH(p,\n      "scheme",TEXTBEFORE(u,"://"),\n      "host",LET(h,TEXTBEFORE(TEXTAFTER(u,"://"),"/"),IFERROR(TEXTBEFORE(h,":"),h)),\n      "path","/"&TEXTBEFORE(TEXTAFTER(TEXTAFTER(u,"://"),"/"),"?"),\n      "query",IFERROR(TEXTAFTER(u,"?"),""),\n      "param",LET(q,IFERROR(TEXTAFTER(u,"?"),""), name,param&"=", IFERROR(TEXTBEFORE(TEXTAFTER("&"&q,"&"&name),"&"),"")),\n      "port",IFERROR(TEXTAFTER(TEXTBEFORE(TEXTAFTER(u,"://"),"/"),":"),""))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
