from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'OUTLIERS'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(values,[method],[threshold],\n  LET(x,TOCOL(values,1), m,IF(ISOMITTED(method),"iqr",LOWER(method)), t,IF(ISOMITTED(threshold),1.5,threshold),\n    med,MEDIAN(x), quart1,QUARTILE.INC(x,1), quart3,QUARTILE.INC(x,3), iqr,quart3-quart1, avg,AVERAGE(x), sd,STDEV.S(x), md,MAD(x),\n    TOROW(MAP(x,LAMBDA(v,SWITCH(m,"zscore",ABS((v-avg)/sd)>t,"mad",ABS(0.6745*(v-med)/md)>t,OR(v<quart1-t*iqr,v>quart3+t*iqr)))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
