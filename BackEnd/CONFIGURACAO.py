# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Serviço de configuração chave/valor — tabela tb_configuracao (MariaDB map).

Uso:
    from BackEnd.app import get_dal
    from BackEnd.CONFIGURACAO import clmain

    cfg = clmain(get_dal())
    cfg._pesquisar_Chave_Configuracao("MINHA_CHAVE")
    cfg._atualizar_Chave_Configuracao("MINHA_CHAVE", "novo_valor")
"""

from __future__ import annotations

from typing import Any

try:
    from LOG import CLLOG
except ImportError:
    from LOG.LOG import CLLOG

_log = CLLOG()
_MODULO = "CONFIGURACAO"
_TABELA = "tb_configuracao"
_MAX_CHAVE = 32
_MAX_VALOR = 255


def _log_evento(descricao: str) -> None:
    _log._registrar_Evento(f"[{_MODULO}] {descricao}")


def _log_excecao(excecao: BaseException, contexto: str) -> None:
    _log._registrar_exceção(excecao, f"[{_MODULO}] {contexto}")


class ConfiguracaoDbError(Exception):
    """Erro ao consultar ou atualizar tb_configuracao."""


class clmain:
    """Cliente para leitura e atualização de chaves em tb_configuracao."""

    def __init__(self, dal: Any) -> None:
        """
        Args:
            dal: instância DAL conectada ao banco map.
        """
        if dal is None:
            raise ConfiguracaoDbError("Instância DAL é obrigatória.")
        self._dal = dal
        _log_evento("Instância clmain inicializada")

    @staticmethod
    def _normalizar_chave(chave: str) -> str:
        ch = (chave or "").strip()
        if not ch:
            raise ConfiguracaoDbError("O argumento 'chave' é obrigatório.")
        if len(ch) > _MAX_CHAVE:
            raise ConfiguracaoDbError(f"A chave excede {_MAX_CHAVE} caracteres.")
        return ch

    @staticmethod
    def _normalizar(chave: str, valor: str) -> tuple[str, str]:
        ch = (chave or "").strip()
        vl = (valor or "").strip()
        if not ch or not vl:
            raise ConfiguracaoDbError("Os argumentos 'chave' e 'valor' são obrigatórios.")
        if len(ch) > _MAX_CHAVE:
            raise ConfiguracaoDbError(f"A chave excede {_MAX_CHAVE} caracteres.")
        if len(vl) > _MAX_VALOR:
            raise ConfiguracaoDbError(f"O valor excede {_MAX_VALOR} caracteres.")
        return ch, vl

    def _pesquisar_Chave_Configuracao(self, chave: str) -> bool:
        """
        Pesquisa em tb_configuracao um registro cuja coluna chave coincida com o
        argumento chave.

        Returns:
            True se encontrado; False em caso de falha ou ausência do registro.
        """
        try:
            ch = self._normalizar_chave(chave)
            _log_evento(f"Pesquisando chave | chave={ch!r}")

            df = self._dal.read(
                f"""
                SELECT idconf
                FROM {_TABELA}
                WHERE chave = ?
                LIMIT 1
                """,
                (ch,),
            )

            if df is None or getattr(df, "empty", True):
                _log_evento(f"Chave não encontrada | chave={ch!r}")
                return False

            _log_evento(f"Pesquisa bem-sucedida | chave={ch!r}")
            return True

        except ConfiguracaoDbError as exc:
            _log_excecao(exc, "_pesquisar_Chave_Configuracao — validação")
            return False
        except Exception as exc:
            _log_excecao(exc, "_pesquisar_Chave_Configuracao")
            return False

    def _obter_Valor_Configuracao(self, chave: str) -> str | None:
        """
        Retorna o valor configurado para a chave informada em tb_configuracao.

        Returns:
            Valor da chave ou None se não encontrada / erro.
        """
        try:
            ch = self._normalizar_chave(chave)
            _log_evento(f"Obtendo valor | chave={ch!r}")

            df = self._dal.read(
                f"""
                SELECT valor
                FROM {_TABELA}
                WHERE chave = ?
                LIMIT 1
                """,
                (ch,),
            )

            if df is None or getattr(df, "empty", True):
                _log_evento(f"Valor não encontrado | chave={ch!r}")
                return None

            valor = str(df.iloc[0]["valor"]).strip()
            _log_evento(f"Valor obtido | chave={ch!r} | valor={valor!r}")
            return valor or None

        except ConfiguracaoDbError as exc:
            _log_excecao(exc, "_obter_Valor_Configuracao — validação")
            return None
        except Exception as exc:
            _log_excecao(exc, "_obter_Valor_Configuracao")
            return None

    def _atualizar_Chave_Configuracao(self, chave: str, valor: str) -> bool:
        """
        Atualiza em tb_configuracao a coluna valor para o registro cuja chave
        coincida com o argumento chave.

        Returns:
            True se a atualização for bem-sucedida; False caso contrário.
        """
        try:
            ch, vl = self._normalizar(chave, valor)
            _log_evento(f"Atualizando chave | chave={ch!r} | valor={vl!r}")

            existe = self._dal.read(
                f"""
                SELECT idconf
                FROM {_TABELA}
                WHERE chave = ?
                LIMIT 1
                """,
                (ch,),
            )
            if existe is None or getattr(existe, "empty", True):
                _log_evento(f"Chave inexistente para atualização | chave={ch!r}")
                return False

            ok = self._dal.update(
                f"""
                UPDATE {_TABELA}
                SET valor = ?
                WHERE chave = ?
                """,
                (vl, ch),
            )
            if not ok:
                _log_evento(f"Falha ao atualizar | chave={ch!r}")
                return False

            _log_evento(f"Atualização bem-sucedida | chave={ch!r} | valor={vl!r}")
            return True

        except ConfiguracaoDbError as exc:
            _log_excecao(exc, "_atualizar_Chave_Configuracao — validação")
            return False
        except Exception as exc:
            _log_excecao(exc, "_atualizar_Chave_Configuracao")
            return False


__all__ = ["clmain", "ConfiguracaoDbError"]
