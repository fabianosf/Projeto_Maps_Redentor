# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Compatibilidade: reexporta o pacote DAL (padrão PROJ_PAD).

A implementação principal está em <raiz>/DAL/DAL.py.
Configurações criptografadas: DAL/arquivos_crip/chave/ e DAL/arquivos_crip/arq/.
"""

from DAL.DAL import (  # noqa: F401
    CONFIG_ARQ_PAD,
    SGBD_PAD,
    ConfigurationError,
    DAL,
    DatabaseConnectionError,
)

__all__ = [
    "DAL",
    "DatabaseConnectionError",
    "ConfigurationError",
    "SGBD_PAD",
    "CONFIG_ARQ_PAD",
]
