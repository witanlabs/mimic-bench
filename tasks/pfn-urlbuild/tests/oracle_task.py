from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'URLBUILD'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3, 4, 5)
LAMBDA_BODY = 'LAMBDA(scheme,host,[path],[query_pairs],[port],\n  LET(p,IF(ISOMITTED(path),"",path), prt,IF(ISOMITTED(port),"",port),\n    base,scheme&"://"&host&IF(prt="","",":"&prt)&IF(p="","","/"&SUBSTITUTE(p," ","%20")),\n    qpart,IFERROR(TEXTJOIN("&",,MAKEARRAY(ROWS(query_pairs),1,LAMBDA(i,j,SUBSTITUTE(INDEX(query_pairs,i,1)," ","%20")&"="&SUBSTITUTE(INDEX(query_pairs,i,2)," ","%20")))),""),\n    IF(qpart="",base,base&"?"&qpart)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
