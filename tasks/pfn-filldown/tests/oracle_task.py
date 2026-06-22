from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'FILLDOWN'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2)
LAMBDA_BODY = 'LAMBDA(array,[axis],\n  LET(a,array, ax,IF(ISOMITTED(axis),"rows",LOWER(axis)), rows,ROWS(a), cols,COLUMNS(a),\n    MAKEARRAY(rows,cols,LAMBDA(r,c,LET(v,INDEX(a,r,c),\n      IF(v<>"",v,IF(ax="cols",\n        LET(pos,IFERROR(MAX(FILTER(SEQUENCE(1,c),MAKEARRAY(1,c,LAMBDA(i,j,INDEX(a,r,j)<>"")))),0),IF(pos=0,"",INDEX(a,r,pos))),\n        LET(pos,IFERROR(MAX(FILTER(SEQUENCE(r),MAKEARRAY(r,1,LAMBDA(i,j,INDEX(a,i,c)<>"")))),0),IF(pos=0,"",INDEX(a,pos,c))))))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
