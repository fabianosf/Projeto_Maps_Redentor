# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Cadastros mestres compartilhados (empresa, linha, turno, local, veículo, motorista)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CadastroError:
    mensagem: str
    codigo: str = "validacao"


# Padrão oficial de frota por empresa (1 letra + 5 dígitos = 6 caracteres).
# Redentor: C47NNN | Futuro: C30NNN | Barra: D13NNN
_REGRAS_FROTA: dict[str, dict[str, str]] = {
    "redentor": {
        "codigo": "C47",
        "regex": r"^C47\d{3}$",
        "exemplo": "C47654",
        "mascara": "C47___",
        "mensagem": "Informe no formato C47 + 3 números. Ex.: C47654.",
    },
    "futuro": {
        "codigo": "C30",
        "regex": r"^C30\d{3}$",
        "exemplo": "C30114",
        "mascara": "C30___",
        "mensagem": "Informe no formato C30 + 3 números. Ex.: C30114.",
    },
    "barra": {
        "codigo": "D13",
        "regex": r"^D13\d{3}$",
        "exemplo": "D13450",
        "mascara": "D13___",
        "mensagem": "Informe no formato D13 + 3 números. Ex.: D13450.",
    },
}

_RE_FROTA_BASICO = re.compile(r"^([A-Za-z])(\d{5})$")


def _rows(dal, sql: str, values: Any = None) -> list[dict[str, Any]]:
    df = dal.read(sql, values) if values is not None else dal.read(sql)
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    out: list[dict[str, Any]] = []
    for row in records:
        clean: dict[str, Any] = {}
        for key, value in row.items():
            if value is None:
                clean[key] = None
            elif hasattr(value, "item"):
                try:
                    clean[key] = value.item()
                except Exception:
                    clean[key] = value
            else:
                clean[key] = value
        out.append(clean)
    return out


def listar_cadastros_mestres(dal) -> dict[str, list[dict[str, Any]]]:
    """Somente registros ativos — usado por Guia, Usuários, etc."""
    return {
        "empresas": _rows(dal, "SELECT * FROM tb_empresa WHERE ativo = 1 ORDER BY codigo_empresa"),
        "linhas": _rows(
            dal,
            """
            SELECT l.*, e.descricao AS empresa
            FROM tb_linha l
            INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
            WHERE l.ativo = 1
            ORDER BY l.codigo_linha
            """,
        ),
        "turnos": _rows(dal, "SELECT * FROM tb_turno WHERE ativo = 1 ORDER BY codigo_turno"),
        "locais": _rows(dal, "SELECT * FROM tb_local WHERE ativo = 1 ORDER BY codigo_local"),
        "veiculos": _rows(
            dal,
            """
            SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa
            FROM tb_veiculo
            WHERE ativo = 1
            ORDER BY SUBSTR(numero_frota, 2), numero_frota
            """,
        ),
        "motoristas": _rows(
            dal,
            """
            SELECT id_motorista, matricula, nome, ativo
            FROM tb_motorista
            WHERE ativo = 1
            ORDER BY CAST(matricula AS UNSIGNED), matricula
            """,
        ),
    }


def _empresa_por_id(dal, id_empresa: int) -> Optional[dict[str, Any]]:
    rows = _rows(
        dal,
        """
        SELECT id_empresa, codigo_empresa, descricao, ativo
        FROM tb_empresa
        WHERE id_empresa = ? AND ativo = 1
        LIMIT 1
        """,
        (int(id_empresa),),
    )
    return rows[0] if rows else None


def _validar_frota_empresa(
    numero_frota: str, empresa_descricao: str
) -> CadastroError | tuple[str, int]:
    """Retorna (frota_normalizada, codigo_veiculo) ou CadastroError."""
    frota = (numero_frota or "").strip().upper()
    chave = (empresa_descricao or "").strip().lower()
    regra = _REGRAS_FROTA.get(chave)

    if not regra:
        if empresa_descricao:
            return CadastroError(
                f"Empresa '{empresa_descricao}' sem padrão de frota configurado.",
                "validacao",
            )
        return CadastroError("Selecione a empresa.", "validacao")

    mensagem = regra["mensagem"]
    if not frota:
        return CadastroError(mensagem, "validacao")
    if len(frota) > 20:
        return CadastroError("Número de frota inválido (máximo 20 caracteres).", "validacao")

    if not re.fullmatch(regra["regex"], frota):
        return CadastroError(mensagem, "frota_fora_faixa")

    m = _RE_FROTA_BASICO.fullmatch(frota)
    if not m:
        return CadastroError(mensagem, "validacao")
    try:
        numero = int(m.group(2))
    except ValueError:
        return CadastroError(mensagem, "validacao")

    return frota, numero


def criar_veiculo(
    dal,
    *,
    numero_frota: str,
    id_empresa: int,
) -> dict[str, Any] | CadastroError:
    """
    Cria veículo vinculado à empresa.
    placa = numero_frota apenas como placeholder (coluna NOT NULL) — não é placa real.
    """
    try:
        id_emp = int(id_empresa)
    except (TypeError, ValueError):
        return CadastroError("Empresa inválida.", "validacao")

    empresa = _empresa_por_id(dal, id_emp)
    if empresa is None:
        return CadastroError("Empresa não encontrada ou inativa.", "validacao")

    validado = _validar_frota_empresa(numero_frota, str(empresa["descricao"]))
    if isinstance(validado, CadastroError):
        return validado
    frota, codigo_veiculo = validado

    existente = _rows(
        dal,
        """
        SELECT id_veiculo, numero_frota, id_empresa
        FROM tb_veiculo
        WHERE UPPER(TRIM(numero_frota)) = ?
        LIMIT 1
        """,
        (frota,),
    )
    if existente:
        return CadastroError(
            f"Já existe veículo com a frota {frota}.",
            "frota_duplicada",
        )

    # placa: placeholder temporário (= frota) — coluna obrigatória UNIQUE; não é placa real
    placa_placeholder = frota[:10]

    ok = dal.create(
        """
        INSERT INTO tb_veiculo (
            codigo_veiculo, numero_frota, placa, ativo, id_empresa
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (codigo_veiculo, frota, placa_placeholder, True, id_emp),
    )
    if not ok:
        again = _rows(
            dal,
            "SELECT id_veiculo FROM tb_veiculo WHERE UPPER(TRIM(numero_frota)) = ? LIMIT 1",
            (frota,),
        )
        if again:
            return CadastroError(
                f"Já existe veículo com a frota {frota}.",
                "frota_duplicada",
            )
        return CadastroError("Falha ao cadastrar o veículo.", "persistencia")

    criado = _rows(
        dal,
        """
        SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa
        FROM tb_veiculo
        WHERE UPPER(TRIM(numero_frota)) = ?
        LIMIT 1
        """,
        (frota,),
    )
    if not criado:
        return CadastroError("Falha ao cadastrar o veículo.", "persistencia")
    return criado[0]
