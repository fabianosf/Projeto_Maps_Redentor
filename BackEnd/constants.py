# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Constantes de negócio — Doc_Proj_Map.odt (RF-RN-004, RF-RN-015)."""

from __future__ import annotations

import secrets
import string

PERFIL_ADMIN = 1
PERFIL_DESPACHANTE = 2
PERFIL_INSPETOR = 3
PERFIS_CONFIG = {PERFIL_ADMIN, PERFIL_INSPETOR}
PERFIS_MAPA = {PERFIL_ADMIN, PERFIL_DESPACHANTE}
COD_MAP_MAX = 99999
COD_MAP_INSERT_RETRIES = 8

# Alfabetos alinhados à política RF-03 / auth_service._PASSWORD_POLICY.
_MAIUSCULAS = string.ascii_uppercase
_MINUSCULAS = string.ascii_lowercase
_DIGITOS = string.digits
_ESPECIAIS = '!@#$%^&*(),.?":{}|<>_-+=[]\\;/`~'
_ALFABETO_SENHA = _MAIUSCULAS + _MINUSCULAS + _DIGITOS + _ESPECIAIS
_SENHA_PROVISORIA_TAMANHO = 12


def _embaralhar(chars: list[str]) -> None:
    """Fisher–Yates com secrets (não usa random.shuffle)."""
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]


def gerar_senha_provisoria(tamanho: int = _SENHA_PROVISORIA_TAMANHO) -> str:
    """
    Senha temporária aleatória (nunca valor fixo).
    Garante: mín. 8, 1 maiúscula, 1 minúscula, 1 dígito, 1 especial.
    """
    n = max(8, int(tamanho))
    obrigatorio = [
        secrets.choice(_MAIUSCULAS),
        secrets.choice(_MINUSCULAS),
        secrets.choice(_DIGITOS),
        secrets.choice(_ESPECIAIS),
    ]
    resto = [secrets.choice(_ALFABETO_SENHA) for _ in range(n - 4)]
    chars = obrigatorio + resto
    _embaralhar(chars)
    return "".join(chars)
