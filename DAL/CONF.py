# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Módulo de leitura de arquivos de configuração criptografados.

Abre arquivos .dat na pasta arquivos_crip/arq/, descriptografa com Fernet +
arquivos_crip/chave/chave.key (mesmo padrão do utilitário PROJ_GAC) e retorna o dicionário de parâmetros.

Uso:
    from CONF import clmain, ConfiguracaoError

    # ou, com a pasta DAL no PYTHONPATH:
    from DAL.CONF import clmain, ConfiguracaoError

    config = clmain()
    parametros = config._obter_Parametros_Configuracao("ad")
    parametros = config._obter_Parametros_Configuracao("seda.dat")
"""

from __future__ import annotations

import json
import os
import traceback
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

try:
    from LOG import CLLOG
except ImportError:
    from LOG.LOG import CLLOG

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DAL_ROOT = _MODULE_DIR

CONF_FOLDER_NAME = "arquivos_crip"
CHAVE_FOLDER_NAME = "chave"
ARQ_FOLDER_NAME = "arq"
KEY_FILE_NAME = "chave.key"

_log = CLLOG()
_MODULO = "CONF"


def _log_evento(descricao: str) -> None:
    _log._registrar_Evento(f"[{_MODULO}] {descricao}")


def _log_excecao(excecao: BaseException, contexto: str) -> None:
    _log._registrar_exceção(excecao, f"[{_MODULO}] {contexto}")


class ConfiguracaoError(Exception):
    """Erro base ao ler ou descriptografar arquivos de configuração."""


class ChaveConfiguracaoNaoEncontradaError(ConfiguracaoError):
    """Arquivo chave.key ausente na pasta de configuração."""


class ArquivoConfiguracaoNaoEncontradoError(ConfiguracaoError):
    """Arquivo .dat solicitado não foi encontrado."""


class ArquivoConfiguracaoVazioError(ConfiguracaoError):
    """Arquivo .dat existe, porém está vazio."""


class DescriptografiaConfiguracaoError(ConfiguracaoError):
    """Falha ao descriptografar o conteúdo (chave inválida ou arquivo corrompido)."""


class JsonConfiguracaoInvalidoError(ConfiguracaoError):
    """Conteúdo descriptografado não é um JSON válido."""


class clmain:
    """
    Cliente para leitura de arquivos de configuração criptografados.

    Utiliza o mesmo algoritmo do PROJ_GAC: Fernet + arquivos_crip/chave/chave.key,
    com arquivos .dat em arquivos_crip/arq/ e conteúdo interno em JSON (dicionário chave/valor).
    """

    def __init__(self, pasta_conf: Optional[str] = None):
        """
        Inicializa o leitor de configuração.

        Args:
            pasta_conf: caminho raiz arquivos_crip/ (contendo subpastas chave/ e arq/).
                        Padrão: <projeto>/DAL/arquivos_crip
        """
        try:
            self._pasta_conf = self._resolver_pasta_conf(pasta_conf)
            self._pasta_chave = os.path.join(self._pasta_conf, CHAVE_FOLDER_NAME)
            self._pasta_arq = os.path.join(self._pasta_conf, ARQ_FOLDER_NAME)
            self._caminho_chave = os.path.join(self._pasta_chave, KEY_FILE_NAME)

            _log_evento(
                f"Inicializado | pasta_conf={self._pasta_conf} | "
                f"pasta_chave={self._pasta_chave} | pasta_arq={self._pasta_arq}"
            )
        except Exception as exc:
            _log_excecao(exc, "Falha ao inicializar leitor de configuração")
            raise

    @staticmethod
    def _resolver_pasta_conf(pasta_conf: Optional[str]) -> str:
        if pasta_conf:
            return os.path.abspath(pasta_conf)
        return os.path.join(_DEFAULT_DAL_ROOT, CONF_FOLDER_NAME)

    @staticmethod
    def _normalizar_nome_arquivo(nome_arquivo: str) -> str:
        nome = (nome_arquivo or "").strip()
        if not nome:
            raise ConfiguracaoError("O nome do arquivo de configuração é obrigatório.")
        if not nome.lower().endswith(".dat"):
            nome += ".dat"
        return nome

    def _carregar_chave(self) -> bytes:
        _log_evento(f"Carregando chave de criptografia | arquivo={self._caminho_chave}")

        if not os.path.exists(self._caminho_chave):
            exc = ChaveConfiguracaoNaoEncontradaError(
                f"Arquivo de chave não encontrado: {self._caminho_chave}"
            )
            _log_excecao(exc, "Chave de configuração não encontrada")
            raise exc

        try:
            with open(self._caminho_chave, "rb") as arquivo_chave:
                chave = arquivo_chave.read()
            if not chave:
                exc = ChaveConfiguracaoNaoEncontradaError(
                    f"Arquivo de chave vazio: {self._caminho_chave}"
                )
                _log_excecao(exc, "Chave de configuração vazia")
                raise exc

            _log_evento(f"Chave carregada com sucesso | arquivo={self._caminho_chave}")
            return chave
        except ConfiguracaoError:
            raise
        except OSError as exc:
            erro = ConfiguracaoError(
                f"Falha ao ler o arquivo de chave '{self._caminho_chave}': {exc}"
            )
            _log_excecao(erro, "Erro de I/O ao ler chave de configuração")
            raise erro from exc

    @staticmethod
    def _descriptografar(conteudo_criptografado: str, chave: bytes) -> str:
        """
        Descriptografa o texto usando Fernet (mesma rotina do PROJ_GAC._crip decrypt).
        """
        if not conteudo_criptografado or not conteudo_criptografado.strip():
            raise ArquivoConfiguracaoVazioError("O arquivo de configuração está vazio.")

        try:
            cipher = Fernet(chave)
            texto_bytes = cipher.decrypt(conteudo_criptografado.encode("utf-8"))
            return texto_bytes.decode("utf-8")
        except InvalidToken as exc:
            raise DescriptografiaConfiguracaoError(
                "Token de criptografia inválido. "
                "O arquivo pode estar corrompido ou a chave.key não corresponde."
            ) from exc
        except Exception as exc:
            raise DescriptografiaConfiguracaoError(
                f"Falha ao descriptografar o arquivo de configuração: {exc}"
            ) from exc

    def _obter_Parametros_Configuracao(self, nome_arquivo: str) -> Dict[str, Any]:
        """
        Lê e descriptografa um arquivo .dat da pasta arquivos_crip/arq/.

        Args:
            nome_arquivo: nome do arquivo (ex.: 'ad', 'ad.dat', 'seda').

        Returns:
            Dicionário com os parâmetros gravados no arquivo.

        Raises:
            ConfiguracaoError: e subclasses em caso de falha na leitura.
        """
        nome_normalizado = self._normalizar_nome_arquivo(nome_arquivo)
        caminho_arquivo = os.path.join(self._pasta_arq, nome_normalizado)

        _log_evento(
            f"Iniciando leitura | arquivo={nome_normalizado} | caminho={caminho_arquivo}"
        )

        if not os.path.exists(caminho_arquivo):
            exc = ArquivoConfiguracaoNaoEncontradoError(
                f"Arquivo '{nome_normalizado}' não encontrado em '{self._pasta_arq}'."
            )
            _log_excecao(
                exc,
                f"Arquivo de configuração não encontrado | arquivo={nome_normalizado}",
            )
            raise exc

        try:
            chave = self._carregar_chave()

            with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
                conteudo_criptografado = arquivo.read()

            _log_evento(
                f"Descriptografando conteúdo | arquivo={nome_normalizado} | "
                f"tamanho_bytes={len(conteudo_criptografado)}"
            )
            json_texto = self._descriptografar(conteudo_criptografado, chave)
            dados = json.loads(json_texto)

            if not isinstance(dados, dict):
                exc = JsonConfiguracaoInvalidoError(
                    f"O conteúdo de '{nome_normalizado}' deve ser um objeto JSON (dicionário)."
                )
                _log_excecao(
                    exc,
                    f"JSON inválido (esperado objeto) | arquivo={nome_normalizado}",
                )
                raise exc

            chaves = sorted(str(k) for k in dados.keys())
            _log_evento(
                f"Leitura concluída com sucesso | arquivo={nome_normalizado} | "
                f"total_chaves={len(chaves)} | chaves={', '.join(chaves)}"
            )
            return dados

        except ConfiguracaoError:
            raise
        except json.JSONDecodeError as exc:
            erro = JsonConfiguracaoInvalidoError(
                f"Falha ao decodificar JSON de '{nome_normalizado}': {exc}"
            )
            _log_excecao(erro, f"JSON malformado | arquivo={nome_normalizado}")
            raise erro from exc
        except OSError as exc:
            erro = ConfiguracaoError(
                f"Falha de I/O ao ler '{caminho_arquivo}': {exc}"
            )
            _log_excecao(erro, f"Erro de I/O | arquivo={nome_normalizado}")
            raise erro from exc
        except Exception as exc:
            erro = ConfiguracaoError(
                f"Erro inesperado ao obter parâmetros de '{nome_normalizado}': {exc}\n"
                f"{traceback.format_exc()}"
            )
            _log_excecao(erro, f"Erro inesperado | arquivo={nome_normalizado}")
            raise erro from exc


__all__ = [
    "clmain",
    "ConfiguracaoError",
    "ChaveConfiguracaoNaoEncontradaError",
    "ArquivoConfiguracaoNaoEncontradoError",
    "ArquivoConfiguracaoVazioError",
    "DescriptografiaConfiguracaoError",
    "JsonConfiguracaoInvalidoError",
]
