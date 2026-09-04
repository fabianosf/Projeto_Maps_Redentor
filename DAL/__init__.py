"""
Pacote DAL — camada de acesso a dados (padrão PROJ_PAD).

Estrutura:
    DAL/
    ├── DAL.py
    ├── CONF.py
    ├── arquivos_crip/
    │   ├── chave/chave.key
    │   └── arq/*.dat
    └── PROJ_GAC/
"""

from .CONF import (
    ArquivoConfiguracaoNaoEncontradoError,
    ArquivoConfiguracaoVazioError,
    ChaveConfiguracaoNaoEncontradaError,
    ConfiguracaoError,
    DescriptografiaConfiguracaoError,
    JsonConfiguracaoInvalidoError,
    clmain,
)
from .DAL import CONFIG_ARQ_PAD, SGBD_PAD, ConfigurationError, DAL, DatabaseConnectionError

__all__ = [
    "DAL",
    "DatabaseConnectionError",
    "ConfigurationError",
    "clmain",
    "ConfiguracaoError",
    "ChaveConfiguracaoNaoEncontradaError",
    "ArquivoConfiguracaoNaoEncontradoError",
    "ArquivoConfiguracaoVazioError",
    "DescriptografiaConfiguracaoError",
    "JsonConfiguracaoInvalidoError",
    "SGBD_PAD",
    "CONFIG_ARQ_PAD",
]
