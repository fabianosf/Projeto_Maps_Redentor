"""Compatibilidade para serviços ERP de funcionários."""

from __future__ import annotations

from typing import Any

from .erp_funcionario_service import (
    MSG_ERP_INDISPONIVEL,
    MSG_FUNCIONARIO_NAO_ENCONTRADO as MSG_ERP_NAO_ENCONTRADA,
    ERPFuncionarioService,
    ErpError,
)


def matricula_existe_erp(
    erp_service: ERPFuncionarioService, matricula: str
) -> bool | ErpError:
    return erp_service.existe(matricula)


def consultar_funcionario_erp(
    erp_service: ERPFuncionarioService, matricula: str
) -> dict[str, Any] | ErpError:
    return erp_service.consultar(matricula)


def anexar_foto_erp(
    erp_service: ERPFuncionarioService, matricula: str, destino: dict[str, Any]
) -> dict[str, Any]:
    destino["foto_base64"] = None
    destino["foto_mime"] = None
    destino["foto_url"] = None
    return erp_service.anexar_foto(matricula, destino)
