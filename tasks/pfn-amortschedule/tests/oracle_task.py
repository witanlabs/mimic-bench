from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'AMORTSCHEDULE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3, 4, 5, 6)
LAMBDA_BODY = 'LAMBDA(rate,nper,pv,[fv],[type],[periods],\n  LET(f,IF(ISOMITTED(fv),0,fv), typ,IF(ISOMITTED(type),0,type), per,IF(ISOMITTED(periods),SEQUENCE(nper),periods),\n    pmt,-PMT(rate,nper,pv,f,typ),\n    HSTACK(per, MAP(per,LAMBDA(p,ROUND(pmt,2))), MAP(per,LAMBDA(p,ROUND(-IPMT(rate,p,nper,pv,f,typ),2))),\n      MAP(per,LAMBDA(p,ROUND(-PPMT(rate,p,nper,pv,f,typ),2))),\n      MAP(per,LAMBDA(p,ROUND(MAX(0,pv-SUM(MAP(SEQUENCE(p),LAMBDA(i,-PPMT(rate,i,nper,pv,f,typ))))),2))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
