# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Constantes de negócio — Doc_Proj_Map.odt (RF-RN-004, RF-RN-015)."""

from __future__ import annotations

import secrets

PERFIL_ADMIN = 1
PERFIL_DESPACHANTE = 2
PERFIL_INSPETOR = 3
PERFIS_CONFIG = {PERFIL_ADMIN, PERFIL_INSPETOR}
PERFIS_MAPA = {PERFIL_ADMIN, PERFIL_DESPACHANTE}
COD_MAP_MAX = 99999
COD_MAP_INSERT_RETRIES = 8


def gerar_senha_provisoria() -> str:
    """Senha temporária segura (não reutilizar valor fixo tipo 12345)."""
    return secrets.token_urlsafe(12)
