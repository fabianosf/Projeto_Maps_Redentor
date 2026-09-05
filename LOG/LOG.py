# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Logger mínimo usado por DAL/CONF/CONFIGURACAO (PROJ_LOG)."""

from __future__ import annotations

import sys
import traceback
from datetime import datetime
from typing import Optional


class CLLOG:
    """API esperada: _registrar_Evento / _registrar_exceção."""

    def __init__(self, destino: Optional[str] = None) -> None:
        self._destino = destino

    def _linha(self, nivel: str, mensagem: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{ts} [{nivel}] {mensagem}"

    def _emitir(self, texto: str) -> None:
        if self._destino:
            try:
                with open(self._destino, "a", encoding="utf-8") as fh:
                    fh.write(texto + "\n")
                return
            except OSError:
                pass
        print(texto, file=sys.stderr)

    def _registrar_Evento(self, descricao: str) -> None:
        self._emitir(self._linha("INFO", str(descricao)))

    def _registrar_exceção(self, excecao: BaseException, contexto: str = "") -> None:
        msg = f"{contexto} | {type(excecao).__name__}: {excecao}".strip(" |")
        self._emitir(self._linha("ERROR", msg))
        tb = "".join(traceback.format_exception(type(excecao), excecao, excecao.__traceback__))
        if tb.strip():
            self._emitir(tb.rstrip())
