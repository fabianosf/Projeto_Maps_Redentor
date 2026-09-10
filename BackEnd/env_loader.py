# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Carrega BackEnd/.env sem sobrescrever variáveis já definidas no ambiente."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_LOADED = False


def load_backend_env(*, force: bool = False) -> Path | None:
    """
    Lê BackEnd/.env (KEY=VALUE) e aplica apenas chaves ainda ausentes em os.environ.
    Não loga valores (podem conter segredos).
    """
    global _LOADED
    if _LOADED and not force:
        return None

    env_path = Path(__file__).resolve().parent / ".env"
    _LOADED = True
    if not env_path.is_file():
        logger.info("Arquivo .env ausente | path=%s", env_path)
        return None

    aplicadas = 0
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if not key or key.startswith("#"):
                continue
            if key in os.environ:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ[key] = value
            aplicadas += 1
    except OSError:
        logger.error("Falha ao ler .env | path=%s", env_path, exc_info=True)
        return env_path

    logger.info(
        "Env carregado | path=%s | chaves_aplicadas=%s",
        env_path.name,
        aplicadas,
    )
    return env_path
