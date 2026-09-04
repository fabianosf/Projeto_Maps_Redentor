# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Contador em memória de tentativas falhas de login por matrícula.

Reinicia ao reiniciar o processo Flask; não persiste em tb_usuario.
"""

from __future__ import annotations

import threading

_tentativas_falhas: dict[str, int] = {}
_lock = threading.Lock()


def obter_tentativas(matricula: str) -> int:
    mat = (matricula or "").strip()
    if not mat:
        return 0
    with _lock:
        return _tentativas_falhas.get(mat, 0)


def registrar_tentativa_falha(matricula: str) -> int:
    """Incrementa e retorna o total de tentativas falhas da matrícula."""
    mat = (matricula or "").strip()
    if not mat:
        return 0
    with _lock:
        total = _tentativas_falhas.get(mat, 0) + 1
        _tentativas_falhas[mat] = total
        return total


def resetar_tentativas(matricula: str) -> None:
    mat = (matricula or "").strip()
    if not mat:
        return
    with _lock:
        _tentativas_falhas.pop(mat, None)


__all__ = ["obter_tentativas", "registrar_tentativa_falha", "resetar_tentativas"]
