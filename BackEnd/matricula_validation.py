# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Validação de matrícula — RF-02, RF-20 (numérica, máx. 5 dígitos)."""

from __future__ import annotations

import re

MATRICULA_MAX_DIGITOS = 5
_MATRICULA = re.compile(r"^\d{1,5}$")


def matricula_valida(matricula: str) -> bool:
    return bool(_MATRICULA.match((matricula or "").strip()))
