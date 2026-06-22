from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'HAVERSINE'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (4, 5)
LAMBDA_BODY = 'LAMBDA(latitude_one,longitude_one,latitude_two,longitude_two,[unit],\n  LET(u,IF(ISOMITTED(unit),"km",LOWER(unit)), radius,SWITCH(u,"mi",3958.7613,"m",6371008.8,6371.0088),\n    phiOne,RADIANS(latitude_one), phiTwo,RADIANS(latitude_two), deltaPhi,RADIANS(latitude_two-latitude_one), deltaLambda,RADIANS(longitude_two-longitude_one),\n    a,SIN(deltaPhi/2)^2+COS(phiOne)*COS(phiTwo)*SIN(deltaLambda/2)^2,\n    ROUND(radius*2*ASIN(MIN(1,SQRT(a))),6)))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
