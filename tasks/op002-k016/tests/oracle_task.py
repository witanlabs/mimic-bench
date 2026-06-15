from __future__ import annotations


TASK_FAMILY = "witan-formula-mixed"
QUERY_BUDGET = 16
ARITY = 2


def formula_for_row(row: int) -> str:
    left = f"A{row}"
    right = f"B{row}"
    return (
        f"=LET(a,{left},b,{right},"
        "IF(ISTEXT(a),"
        'UPPER(TRIM(a))&":"&TEXT(LEN(TRIM(b&"")),"0"),'
        "IF(ISTEXT(b),"
        'LOWER(TRIM(b))&":"&TEXT(ROUND(a+LEN(TRIM(b)),9),"0.#########"),'
        "ROUND((a+1)*(b-2),9))))"
    )
