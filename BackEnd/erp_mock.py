# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Mock local de funcionários ERP — SOMENTE com ERP_PROVIDER=mock (testes).

Não inclui matrículas reais de produção/admin (59492, 59817).
Produção deve usar ERP_PROVIDER=oracle + Globus.flp_funcionarios.
"""

from __future__ import annotations

from typing import Any

from .erp_service import ErpError
from .matricula_validation import matricula_valida

MSG_MATRICULA_INVALIDA = "Matrícula deve ser numérica com no máximo 5 dígitos."
MSG_FUNCIONARIO_NAO_ENCONTRADO = "Matrícula não encontrada no cadastro de funcionários."

# Matrículas sintéticas apenas para testes locais (ERP_PROVIDER=mock).
FUNCIONARIOS_MOCK: dict[str, str] = {
    "59800": "Jose Ricardo",
    "59700": "Mauro Naves",
    "59600": "Julio Teixeira",
    "59500": "Pedro Alencar",
}


def consultar_funcionario_mock(matricula: str) -> dict[str, Any] | ErpError:
    """
    Mesmo formato legado de consulta mock:
    {cod_func, nome, foto_base64, foto_mime}.
    """
    matricula = (matricula or "").strip()
    if not matricula_valida(matricula):
        return ErpError(MSG_MATRICULA_INVALIDA, "validacao")

    chave = matricula.lstrip("0") or "0"
    nome = FUNCIONARIOS_MOCK.get(matricula) or FUNCIONARIOS_MOCK.get(chave.zfill(5))
    if nome is None and matricula.isdigit():
        nome = FUNCIONARIOS_MOCK.get(str(int(matricula)))

    if nome is None:
        return ErpError(MSG_FUNCIONARIO_NAO_ENCONTRADO, "funcionario_nao_encontrado")

    return {
        "cod_func": matricula,
        "nome": nome,
        "foto_base64": None,
        "foto_mime": None,
    }
