from __future__ import annotations


TASK_FAMILY = "witan-formula"
QUERY_BUDGET = 16
ARITY = 2


def formula_for_row(row: int) -> str:
    left = f"A{row}"
    right = f"B{row}"
    return (
        f"=LET(a,{left},b,{right},"
        "IF(a<0,SQRT(-1),ROUND(((a*a)+(2*b))/b,9)))"
    )
