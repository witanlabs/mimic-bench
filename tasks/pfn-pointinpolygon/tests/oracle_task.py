from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'POINTINPOLYGON'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3,)
LAMBDA_BODY = 'LAMBDA(lat,lon,polygon,\n  LET(poly,polygon, n,ROWS(poly),\n    REDUCE(FALSE,SEQUENCE(n),LAMBDA(acc,i,\n      LET(j,IF(i=1,n,i-1), yi,INDEX(poly,i,1), xi,INDEX(poly,i,2), yj,INDEX(poly,j,1), xj,INDEX(poly,j,2),\n        crosses,IF(xj=xi,FALSE,AND((xi>lon)<>(xj>lon),lat<(yj-yi)*(lon-xi)/(xj-xi)+yi)),\n        IF(crosses,NOT(acc),acc))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
