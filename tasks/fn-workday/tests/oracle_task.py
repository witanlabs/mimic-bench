from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'WORKDAY'
TASK_FAMILY = "witan-function"
ARG_MODE = "formula_literals"
ARITIES = (2, 3, 4)


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    return f"={FUNCTION_NAME}(" + ",".join(args) + ")"
