from __future__ import annotations

from typing import Any


FUNCTION_NAME = 'STRIPDIACRITICS'
TASK_FAMILY = "proposed-function"
ARG_MODE = "formula_literals"
ARITIES = (1,)
LAMBDA_BODY = 'LAMBDA(text,\n  LET(src,{"á","à","â","ä","ã","å","ā","ă","ą","ç","ć","č","ď","é","è","ê","ë","ē","ė","ę","í","ì","î","ï","ī","ł","ñ","ń","ó","ò","ô","ö","õ","ø","ō","ř","ś","š","ť","ú","ù","û","ü","ū","ý","ÿ","ž","ż","Á","À","Â","Ä","Ã","Å","Ç","É","È","Ê","Ë","Í","Ì","Î","Ï","Ñ","Ó","Ò","Ô","Ö","Õ","Ø","Ú","Ù","Û","Ü","Ý","Ž","Ż"},\n      dst,{"a","a","a","a","a","a","a","a","a","c","c","c","d","e","e","e","e","e","e","e","i","i","i","i","i","l","n","n","o","o","o","o","o","o","o","r","s","s","t","u","u","u","u","u","y","y","z","z","A","A","A","A","A","A","C","E","E","E","E","I","I","I","I","N","O","O","O","O","O","O","U","U","U","U","Y","Z","Z"},\n      REDUCE(text,SEQUENCE(COLUMNS(src)),LAMBDA(acc,i,SUBSTITUTE(acc,INDEX(src,i),INDEX(dst,i))))))'


def formula_for_args(args: Any) -> str:
    if not isinstance(args, list) or len(args) not in ARITIES:
        raise ValueError("bad_arity")
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("arguments_must_be_formula_literals")
    call = f"{FUNCTION_NAME}(" + ",".join(args) + ")"
    return f"=LET({FUNCTION_NAME},{LAMBDA_BODY},{call})"
