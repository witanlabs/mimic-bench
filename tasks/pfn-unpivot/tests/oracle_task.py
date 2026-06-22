from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'UNPIVOT'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (3, 4, 5)
LAMBDA_BODY = 'LAMBDA(table,id_cols,value_cols,[name_header],[value_header],\n  LET(t,table, ids,TOROW(id_cols), vals,TOROW(value_cols), ih,COLUMNS(ids), vh,COLUMNS(vals),\n    nh,IF(ISOMITTED(name_header),"attribute",name_header), valh,IF(ISOMITTED(value_header),"value",value_header),\n    MAKEARRAY((ROWS(t)-1)*vh+1,ih+2,LAMBDA(r,c,\n      IF(r=1,IF(c<=ih,INDEX(t,1,INDEX(ids,1,c)),IF(c=ih+1,nh,valh)),\n        LET(srcRow,QUOTIENT(r-2,vh)+2, valPos,MOD(r-2,vh)+1, valCol,INDEX(vals,1,valPos),\n          IF(c<=ih,INDEX(t,srcRow,INDEX(ids,1,c)),IF(c=ih+1,INDEX(t,1,valCol),INDEX(t,srcRow,valCol)))))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
