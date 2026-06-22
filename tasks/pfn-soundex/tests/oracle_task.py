from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'SOUNDEX'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1,)
LAMBDA_BODY = 'LAMBDA(text,\n  IF(text="",VALUE(""),\n  LET(s,UPPER(text), ch,MID(s,SEQUENCE(LEN(s)),1),\n    code,MAP(ch,LAMBDA(x,SWITCH(TRUE,\n      ISNUMBER(XMATCH(x,{"B","F","P","V"})),"1",\n      ISNUMBER(XMATCH(x,{"C","G","J","K","Q","S","X","Z"})),"2",\n      ISNUMBER(XMATCH(x,{"D","T"})),"3",\n      x="L","4",ISNUMBER(XMATCH(x,{"M","N"})),"5",x="R","6",""))),\n    first,LEFT(s,1), tail,DROP(code,1), prev,DROP(code,-1),\n    LEFT(first&TEXTJOIN("",,FILTER(tail,(tail<>"")*(tail<>prev)))&"000",4))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
