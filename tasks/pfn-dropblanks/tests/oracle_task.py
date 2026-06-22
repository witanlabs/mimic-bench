from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'DROPBLANKS'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1, 2, 3)
LAMBDA_BODY = 'LAMBDA(array,[axis],[mode],\n  LET(a,array, ax,IF(ISOMITTED(axis),"rows",LOWER(axis)), m,IF(ISOMITTED(mode),"all",LOWER(mode)),\n    keepRows,BYROW(a,LAMBDA(r,IF(m="any",SUM(--(r<>""))=COLUMNS(r),SUM(--(r<>""))>0))),\n    keepCols,BYCOL(a,LAMBDA(c,IF(m="any",SUM(--(c<>""))=ROWS(c),SUM(--(c<>""))>0))),\n    IFERROR(IF(ax="cols",TRANSPOSE(FILTER(TRANSPOSE(a),TRANSPOSE(keepCols))),FILTER(a,keepRows)),VALUE(""))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
