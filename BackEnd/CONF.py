# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Compatibilidade: reexporta CONF do pacote DAL (padrão PROJ_PAD).

Configurações: DAL/arquivos_crip/chave/chave.key + DAL/arquivos_crip/arq/*.dat
"""

from DAL.CONF import (  # noqa: F401
    ArquivoConfiguracaoNaoEncontradoError,
    ArquivoConfiguracaoVazioError,
    ChaveConfiguracaoNaoEncontradaError,
    ConfiguracaoError,
    DescriptografiaConfiguracaoError,
    JsonConfiguracaoInvalidoError,
    clmain,
)

__all__ = [
    "clmain",
    "ConfiguracaoError",
    "ChaveConfiguracaoNaoEncontradaError",
    "ArquivoConfiguracaoNaoEncontradoError",
    "ArquivoConfiguracaoVazioError",
    "DescriptografiaConfiguracaoError",
    "JsonConfiguracaoInvalidoError",
]
