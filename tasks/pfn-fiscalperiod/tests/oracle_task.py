from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'FISCALPERIOD'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(date,[year_start_month],[return_type],\n  LET(d,DATEVALUE(date), sm,IF(ISOMITTED(year_start_month),1,year_start_month), rt,IF(ISOMITTED(return_type),"label",LOWER(return_type)),\n    off,MOD(MONTH(d)-sm,12), fy,YEAR(d)+(MONTH(d)>=sm), fq,QUOTIENT(off,3)+1, fm,off+1,\n    SWITCH(rt,"year",fy,"quarter",fq,"month",fm,"FY"&fy&"-Q"&fq)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
