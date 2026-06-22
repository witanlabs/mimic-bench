from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'CROSSTAB'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3, 4)
LAMBDA_BODY = 'LAMBDA(row_labels,col_labels,[values],[agg],\n  LET(r,TOCOL(row_labels), c,TOCOL(col_labels), ur,UNIQUE(r), uc,UNIQUE(c),\n    VSTACK(HSTACK("",TRANSPOSE(uc)),\n      HSTACK(ur,MAKEARRAY(ROWS(ur),ROWS(uc),LAMBDA(i,j,SUM(--(r=INDEX(ur,i))*--(c=INDEX(uc,j)))))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
