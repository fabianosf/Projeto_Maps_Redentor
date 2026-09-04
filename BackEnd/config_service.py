# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Parâmetros de configuração persistidos em tb_configuracao."""

from __future__ import annotations

from dataclasses import dataclass

from .CONFIGURACAO import clmain
from .auth_service import obter_qtd_max_tentativas

QTD_MAX_TENTATIVAS_CHAVE = "QTD_MAX_TENTATIVAS"
BLOQUEIO_TENTATIVAS_CHAVE = "BLOQUEIO_TENTATIVAS_LOGIN"


@dataclass(frozen=True)
class ServiceError:
    mensagem: str
    codigo: str = "erro_negocio"


def _salvar_chave(dal, chave: str, valor: str) -> bool:
    cfg = clmain(dal)
    if cfg._pesquisar_Chave_Configuracao(chave):
        return bool(cfg._atualizar_Chave_Configuracao(chave, valor))
    return bool(
        dal.create(
            "INSERT INTO tb_configuracao (chave, valor) VALUES (?, ?)",
            (chave, valor),
        )
    )


def obter_bloqueio_tentativas(dal) -> bool:
    cfg = clmain(dal)
    if not cfg._pesquisar_Chave_Configuracao(BLOQUEIO_TENTATIVAS_CHAVE):
        return True
    return cfg._obter_Valor_Configuracao(BLOQUEIO_TENTATIVAS_CHAVE) == "1"


def obter_config_login(dal) -> dict[str, str | bool]:
    return {
        "qtd_max_tentativas": str(obter_qtd_max_tentativas(dal)),
        "bloqueio_tentativas": obter_bloqueio_tentativas(dal),
    }


def obter_qtd_tentativas(dal) -> str:
    return str(obter_qtd_max_tentativas(dal))


def salvar_config_login(
    dal,
    valor_qtd: str,
    bloqueio_ativo: bool,
) -> dict[str, str | bool] | ServiceError:
    valor_qtd = (valor_qtd or "").strip()
    if not valor_qtd.isdigit():
        return ServiceError("Informe um valor numérico para Qtd/T.", "validacao")
    qtd = int(valor_qtd)
    if qtd <= 0 or qtd > 9:
        return ServiceError("QTD deve estar entre 1 e 9.", "validacao")

    if not _salvar_chave(dal, QTD_MAX_TENTATIVAS_CHAVE, str(qtd)):
        return ServiceError("Não foi possível salvar a configuração.", "persistencia")
    if not _salvar_chave(dal, BLOQUEIO_TENTATIVAS_CHAVE, "1" if bloqueio_ativo else "0"):
        return ServiceError("Não foi possível salvar a configuração.", "persistencia")

    return {
        "qtd_max_tentativas": str(qtd),
        "bloqueio_tentativas": bloqueio_ativo,
    }


def salvar_qtd_tentativas(dal, valor: str) -> str | ServiceError:
    resultado = salvar_config_login(dal, valor, obter_bloqueio_tentativas(dal))
    if isinstance(resultado, ServiceError):
        return resultado
    return str(resultado["qtd_max_tentativas"])
