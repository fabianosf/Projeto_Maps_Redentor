# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Cadastros mestres compartilhados (empresa, linha, turno, local, veículo, motorista)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CadastroError:
    mensagem: str
    codigo: str = "validacao"


# Validação genérica de frota (independente da empresa).
# Aceita apenas: 47xxx | 30xxx | 13xxx (cinco dígitos).
# Configurável via tb_configuracao / env: FROTA_REGEX, FROTA_MAX_LEN, FROTA_EXEMPLO, FROTA_MENSAGEM.
_FROTA_REGEX_DEFAULT = r"^(47|30|13)[0-9]{3}$"
_FROTA_MAX_LEN_DEFAULT = 5
_FROTA_EXEMPLO_DEFAULT = "47123"
_FROTA_MENSAGEM_DEFAULT = (
    "Informe um carro válido: 47xxx, 30xxx ou 13xxx. "
    "Exemplos: 47123, 30123 ou 13123."
)


def _cfg_valor(dal, chave: str) -> Optional[str]:
    try:
        rows = _rows(
            dal,
            "SELECT valor FROM tb_configuracao WHERE chave = ? LIMIT 1",
            (chave,),
        )
        if rows and rows[0].get("valor") is not None:
            texto = str(rows[0]["valor"]).strip()
            return texto or None
    except Exception:
        pass
    env = os.environ.get(chave)
    if env is not None and str(env).strip():
        return str(env).strip()
    return None


def obter_regra_frota(dal=None) -> dict[str, Any]:
    """Regra genérica de frota (sem vínculo com empresa)."""
    regex = _FROTA_REGEX_DEFAULT
    max_len = _FROTA_MAX_LEN_DEFAULT
    exemplo = _FROTA_EXEMPLO_DEFAULT
    mensagem = _FROTA_MENSAGEM_DEFAULT
    if dal is not None:
        regex = _cfg_valor(dal, "FROTA_REGEX") or regex
        exemplo = _cfg_valor(dal, "FROTA_EXEMPLO") or exemplo
        mensagem = _cfg_valor(dal, "FROTA_MENSAGEM") or mensagem
        raw_max = _cfg_valor(dal, "FROTA_MAX_LEN")
        if raw_max:
            try:
                max_len = max(1, min(40, int(raw_max)))
            except (TypeError, ValueError):
                pass
    return {
        "regex": regex,
        "max_len": max_len,
        "exemplo": exemplo,
        "mensagem": mensagem,
        "placeholder": f"Ex.: {exemplo}",
        "mascara": None,
    }


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


def listar_cadastros_mestres(dal) -> dict[str, Any]:
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
            ORDER BY numero_frota
            """,
        ),
        "motoristas": _rows(
            dal,
            """
            SELECT id_motorista, matricula, nome, ativo
            FROM tb_motorista
            WHERE ativo = 1
            ORDER BY matricula
            """,
        ),
        "frota_regra": obter_regra_frota(dal),
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


def _proximo_codigo_veiculo(dal) -> int:
    rows = _rows(dal, "SELECT COALESCE(MAX(codigo_veiculo), 0) AS m FROM tb_veiculo")
    try:
        return int(rows[0]["m"]) + 1 if rows else 1
    except (TypeError, ValueError, KeyError):
        return 1


def validar_frota(
    numero_frota: str, dal=None
) -> CadastroError | tuple[str, int]:
    """
    Valida frota genérica (única, formato configurável).
    Retorna (frota_normalizada, codigo_veiculo_sugerido) ou CadastroError.
    Não depende da empresa.
    """
    regra = obter_regra_frota(dal)
    frota = (numero_frota or "").strip().upper()
    mensagem = str(regra["mensagem"])
    max_len = int(regra["max_len"])

    if not frota:
        return CadastroError(mensagem, "validacao")
    if len(frota) > max_len:
        return CadastroError(mensagem, "frota_invalida")
    try:
        padrao = re.compile(str(regra["regex"]))
    except re.error:
        padrao = re.compile(_FROTA_REGEX_DEFAULT)
    if not padrao.fullmatch(frota):
        return CadastroError(mensagem, "frota_invalida")

    # codigo_veiculo: dígitos da frota quando houver; senão próximo sequencial.
    digitos = re.sub(r"\D", "", frota)
    if digitos:
        try:
            codigo = int(digitos[-9:])
            if codigo > 0:
                return frota, codigo
        except ValueError:
            pass
    if dal is not None:
        return frota, _proximo_codigo_veiculo(dal)
    return frota, abs(hash(frota)) % 1_000_000_000 or 1


# Compat: nome antigo usado por mapa_service / testes legados.
def _validar_frota_empresa(
    numero_frota: str, empresa_descricao: str = ""
) -> CadastroError | tuple[str, int]:
    """Compat: ignora empresa; valida formato genérico."""
    del empresa_descricao
    return validar_frota(numero_frota, dal=None)


def criar_veiculo(
    dal,
    *,
    numero_frota: str,
    id_empresa: int | None = None,
) -> dict[str, Any] | CadastroError:
    """
    Cria veículo independente (identificador único = numero_frota).
    id_empresa é opcional/informativo — não amarra o formato da frota.
    """
    id_emp: int | None = None
    if id_empresa is not None and str(id_empresa).strip() not in ("", "null", "None"):
        try:
            id_emp = int(id_empresa)
        except (TypeError, ValueError):
            return CadastroError("Empresa inválida.", "validacao")
        empresa = _empresa_por_id(dal, id_emp)
        if empresa is None:
            return CadastroError("Empresa não encontrada ou inativa.", "validacao")

    validado = validar_frota(numero_frota, dal=dal)
    if isinstance(validado, CadastroError):
        return validado
    frota, codigo_sugerido = validado

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

    # Evita colisão de codigo_veiculo UNIQUE
    codigo_veiculo = codigo_sugerido
    colisao = _rows(
        dal,
        "SELECT id_veiculo FROM tb_veiculo WHERE codigo_veiculo = ? LIMIT 1",
        (codigo_veiculo,),
    )
    if colisao:
        codigo_veiculo = _proximo_codigo_veiculo(dal)

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
