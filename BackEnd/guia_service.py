# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Tela Guia — CRUD tb_guia."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

_HHMM = re.compile(r"^\d{2}:\d{2}$")


@dataclass(frozen=True)
class GuiaError:
    mensagem: str
    codigo: str = "guia_error"


def _parse_int_opcional(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _id_veiculo_por_frota(dal, numero: str) -> Optional[int]:
    numero = (numero or "").strip()
    if not numero:
        return None
    df = dal.read(
        "SELECT id_veiculo FROM tb_veiculo WHERE ativo = 1 AND numero_frota = ? LIMIT 1",
        (numero,),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_veiculo"])


def _id_motorista_por_matricula(dal, matricula: str) -> Optional[int]:
    matricula = (matricula or "").strip()
    if not matricula:
        return None
    df = dal.read(
        "SELECT id_motorista FROM tb_motorista WHERE ativo = 1 AND matricula = ? LIMIT 1",
        (matricula,),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_motorista"])


def _data_br_para_sql(data_br: str) -> Optional[str]:
    data_br = (data_br or "").strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", data_br)
    if not m:
        return None
    try:
        datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"


def _datetime_guia(data_sql: Optional[str], hhmm: Optional[str]) -> Optional[str]:
    if not data_sql or not hhmm or not _HHMM.match(hhmm):
        return None
    return f"{data_sql} {hhmm}:00"


def _data_cadastro_agora() -> str:
    """Data/hora do cadastro persistida em tb_guia.data (DATETIME)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _row_guia(dal, id_guia: int) -> Optional[dict[str, Any]]:
    df = dal.read(
        """
        SELECT g.*, v.numero_frota, m.matricula AS matricula_motorista,
               t.descricao AS turno_descricao,
               l.codigo_linha AS linha_codigo,
               l.descricao AS linha_descricao
        FROM tb_guia g
        LEFT JOIN tb_veiculo v ON v.id_veiculo = g.id_veiculo
        LEFT JOIN tb_motorista m ON m.id_motorista = g.id_motorista
        LEFT JOIN tb_turno t ON t.id_turno = g.id_turno
        LEFT JOIN tb_linha l ON l.id_linha = g.id_linha
        WHERE g.id_guia = ?
        """,
        (id_guia,),
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def buscar_por_numero(dal, numero: str) -> dict[str, Any] | GuiaError:
    numero = (numero or "").strip()
    if not numero:
        return GuiaError("Informe o número da guia.", "validacao")
    df = dal.read(
        """
        SELECT g.*, v.numero_frota, m.matricula AS matricula_motorista,
               t.descricao AS turno_descricao,
               l.codigo_linha AS linha_codigo,
               l.descricao AS linha_descricao
        FROM tb_guia g
        LEFT JOIN tb_veiculo v ON v.id_veiculo = g.id_veiculo
        LEFT JOIN tb_motorista m ON m.id_motorista = g.id_motorista
        LEFT JOIN tb_turno t ON t.id_turno = g.id_turno
        LEFT JOIN tb_linha l ON l.id_linha = g.id_linha
        WHERE g.numero = ?
        """,
        (numero,),
    )
    if df.empty:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    return df.iloc[0].to_dict()


def listar_guias(dal, data_br: Optional[str] = None) -> list[dict[str, Any]] | GuiaError:
    """
    Lista guias do dia (filtro opcional dd/mm/aaaa).
    Endpoint aditivo — não altera contratos existentes.
    """
    params: tuple[Any, ...] = ()
    where = ""
    if data_br is not None and str(data_br).strip():
        data_sql = _data_br_para_sql(str(data_br).strip())
        if not data_sql:
            return GuiaError("Data inválida.", "validacao")
        where = """
            WHERE DATE(COALESCE(g.hor_ini, g.hor_fim, g.data)) = ?
        """
        params = (data_sql,)

    df = dal.read(
        f"""
        SELECT g.*, v.numero_frota, m.matricula AS matricula_motorista,
               t.descricao AS turno_descricao,
               l.codigo_linha AS linha_codigo,
               l.descricao AS linha_descricao
        FROM tb_guia g
        LEFT JOIN tb_veiculo v ON v.id_veiculo = g.id_veiculo
        LEFT JOIN tb_motorista m ON m.id_motorista = g.id_motorista
        LEFT JOIN tb_turno t ON t.id_turno = g.id_turno
        LEFT JOIN tb_linha l ON l.id_linha = g.id_linha
        {where}
        ORDER BY COALESCE(g.hor_ini, g.data) ASC, g.id_guia ASC
        """,
        params if params else None,
    )
    if df is None or getattr(df, "empty", True):
        return []
    return df.to_dict(orient="records")


def _montar_observacao_execucao(body: dict[str, Any], obs_base: str) -> str | GuiaError:
    """Concatena ocorrências / pas. IDA-VOLTA na observação (limite 150)."""
    partes: list[str] = []
    if obs_base:
        partes.append(obs_base)

    ocorrencias = str(body.get("ocorrencias", "")).strip()
    if ocorrencias:
        partes.append(f"Ocorr:{ocorrencias}")

    pas_ida = body.get("pas_ida", body.get("viagens_ida"))
    pas_volta = body.get("pas_volta", body.get("viagens_volta"))
    extras: list[str] = []
    for label, valor in (("IDA", pas_ida), ("VOLTA", pas_volta)):
        if valor is None or str(valor).strip() == "":
            continue
        try:
            n = int(valor)
        except (TypeError, ValueError):
            return GuiaError(f"Viagens {label} inválidas.", "validacao")
        if n < 0:
            return GuiaError(f"Viagens {label} inválidas.", "validacao")
        extras.append(f"{label}={n}")
    if extras:
        partes.append("[" + " ".join(extras) + "]")

    obs = " | ".join(partes).strip()
    if len(obs) > 150:
        return GuiaError("Observação deve ter no máximo 150 caracteres.", "validacao")
    return obs


def _aplicar_contexto_escala(dal, body: dict[str, Any]) -> dict[str, Any] | GuiaError:
    """Quando id_item_map informado, preenche vínculos da escala (fonte Mapa)."""
    id_item = _parse_int_opcional(body.get("id_item_map", body.get("id_item")))
    if not id_item:
        return body

    from .guia_escala_service import obter_contexto_escala

    ctx = obter_contexto_escala(dal, id_item)
    if isinstance(ctx, GuiaError):
        return ctx

    data_ctx = ctx.get("data")
    data_body = str(body.get("data", "")).strip()
    return {
        **body,
        "id_item_map": id_item,
        "data": data_body or data_ctx or body.get("data"),
        "id_empresa": ctx.get("id_empresa"),
        "id_linha": ctx.get("id_linha"),
        "id_turno": ctx.get("id_turno"),
        "id_veiculo": ctx.get("id_veiculo"),
        "id_motorista": ctx.get("id_motorista"),
        "numero_frota": ctx.get("numero_frota") or body.get("numero_frota"),
        "matricula_motorista": ctx.get("matricula_motorista")
        or body.get("matricula_motorista"),
        "carro": ctx.get("numero_frota") or body.get("carro"),
        "motorista": ctx.get("matricula_motorista") or body.get("motorista"),
        "cod_map": ctx.get("cod_map"),
        "codigo_mapa": ctx.get("codigo_mapa"),
    }


def _gerar_numero_guia(dal, body: dict[str, Any]) -> str:
    """
    Gera NR(Guia) único (máx. 15). Preferência: codigo_mapa/cod_map + frota;
    fallback temporal. Preserva envio manual quando o cliente informa numero.
    """
    codigo_mapa = str(body.get("codigo_mapa") or "").strip()
    cod = body.get("cod_map")
    frota = str(body.get("numero_frota") or body.get("carro") or "").strip()
    id_item = _parse_int_opcional(body.get("id_item_map", body.get("id_item")))

    partes: list[str] = []
    if codigo_mapa:
        partes.append(re.sub(r"[^\w]", "", codigo_mapa)[:8])
    elif cod is not None and str(cod).strip() != "":
        try:
            partes.append(str(int(cod)))
        except (TypeError, ValueError):
            partes.append(str(cod).strip()[:5])
    if frota:
        partes.append(re.sub(r"\D", "", frota)[:5] or frota[:5])
    if id_item and not partes:
        partes.append(str(id_item))
    base = "".join(partes).strip()
    if not base:
        base = datetime.now().strftime("%y%m%d%H%M%S")
    base = re.sub(r"[^\w]", "", base)[:15] or datetime.now().strftime("%y%m%d%H%M%S")

    candidato = base
    seq = 0
    while True:
        existe = dal.read(
            "SELECT id_guia FROM tb_guia WHERE numero = ?",
            (candidato,),
        )
        if existe is None or getattr(existe, "empty", True):
            return candidato
        seq += 1
        sufixo = str(seq)
        candidato = (base[: max(1, 15 - len(sufixo))] + sufixo)[:15]


def _validar_payload(
    body: dict[str, Any], *, permitir_numero_vazio: bool = False
) -> GuiaError | dict[str, Any]:
    numero = str(body.get("numero", "")).strip()
    if not numero and not permitir_numero_vazio:
        return GuiaError("NR(Guia) é obrigatório.", "validacao")
    if numero and len(numero) > 15:
        return GuiaError("NR(Guia) deve ter no máximo 15 caracteres.", "validacao")

    data_sql = _data_br_para_sql(str(body.get("data", "")))
    if not data_sql:
        return GuiaError("Data inválida.", "validacao")

    hor_ini = str(body.get("hor_ini", body.get("horario_pegada", ""))).strip()
    hor_fim = str(body.get("hor_fim", body.get("horario_largada", ""))).strip()
    if hor_ini and not _HHMM.match(hor_ini):
        return GuiaError("INÍCIO(JORNADA) inválido.", "validacao")
    if hor_fim and not _HHMM.match(hor_fim):
        return GuiaError("FIM(JORNADA) inválido.", "validacao")

    obs_base = str(body.get("observacao", "")).strip()
    obs = _montar_observacao_execucao(body, obs_base)
    if isinstance(obs, GuiaError):
        return obs

    numero_frota = str(body.get("numero_frota", body.get("carro", ""))).strip()
    matricula_motorista = str(
        body.get("matricula_motorista", body.get("motorista", ""))
    ).strip()
    if numero_frota and (not numero_frota.isdigit() or len(numero_frota) > 5):
        return GuiaError("Carro deve conter até 5 dígitos numéricos.", "validacao")
    if matricula_motorista and (
        not matricula_motorista.isdigit() or len(matricula_motorista) > 5
    ):
        return GuiaError("Motorista deve conter até 5 dígitos numéricos.", "validacao")

    return {
        "numero": numero,
        "data_sql": data_sql,
        "id_empresa": _parse_int_opcional(body.get("id_empresa")),
        "id_linha": _parse_int_opcional(body.get("id_linha")),
        "id_turno": _parse_int_opcional(body.get("id_turno")),
        "id_veiculo": _parse_int_opcional(body.get("id_veiculo")),
        "id_motorista": _parse_int_opcional(body.get("id_motorista")),
        "id_item_map": _parse_int_opcional(body.get("id_item_map", body.get("id_item"))),
        "numero_frota": numero_frota,
        "matricula_motorista": matricula_motorista,
        "hor_ini": hor_ini,
        "hor_fim": hor_fim,
        "roleta01_ini": _parse_int_opcional(
            body.get(
                "roleta01_ini",
                body.get(
                    "roleta01_inicial",
                    body.get("roleta_ini", body.get("roleta_inicial")),
                ),
            )
        ),
        "roleta01_fim": _parse_int_opcional(
            body.get(
                "roleta01_fim",
                body.get(
                    "roleta01_final",
                    body.get("roleta_fim", body.get("roleta_final")),
                ),
            )
        ),
        "roleta2_ini": _parse_int_opcional(
            body.get("roleta2_ini", body.get("roleta2_inicial"))
        ),
        "roleta2_fim": _parse_int_opcional(
            body.get("roleta2_fim", body.get("roleta2_final"))
        ),
        "observacao": obs or None,
    }


def _resolver_vinculos(dal, dados: dict[str, Any]) -> GuiaError | dict[str, Any]:
    id_veiculo = dados["id_veiculo"]
    if not id_veiculo and dados["numero_frota"]:
        id_veiculo = _id_veiculo_por_frota(dal, dados["numero_frota"])
        if id_veiculo is None:
            return GuiaError("Carro não encontrado.", "carro_invalido")

    id_motorista = dados["id_motorista"]
    if not id_motorista and dados["matricula_motorista"]:
        id_motorista = _id_motorista_por_matricula(dal, dados["matricula_motorista"])
        if id_motorista is None:
            return GuiaError("Motorista não encontrado.", "motorista_invalido")

    dados = {**dados, "id_veiculo": id_veiculo, "id_motorista": id_motorista}
    return dados


def criar_guia(dal, body: dict[str, Any]) -> dict[str, Any] | GuiaError:
    body_ctx = _aplicar_contexto_escala(dal, body)
    if isinstance(body_ctx, GuiaError):
        return body_ctx

    numero_informado = str(body_ctx.get("numero", "")).strip()
    if not numero_informado:
        body_ctx = {**body_ctx, "numero": _gerar_numero_guia(dal, body_ctx)}

    validado = _validar_payload(body_ctx)
    if isinstance(validado, GuiaError):
        return validado
    dados = _resolver_vinculos(dal, validado)
    if isinstance(dados, GuiaError):
        return dados

    existe = dal.read(
        "SELECT id_guia FROM tb_guia WHERE numero = ?",
        (dados["numero"],),
    )
    if not existe.empty:
        if numero_informado:
            return GuiaError("NR(Guia) já cadastrado.", "numero_duplicado")
        # regenera uma vez se colisão após geração automática
        novo = _gerar_numero_guia(dal, {**body_ctx, **dados})
        dados = {**dados, "numero": novo}
        existe2 = dal.read(
            "SELECT id_guia FROM tb_guia WHERE numero = ?",
            (dados["numero"],),
        )
        if not existe2.empty:
            return GuiaError("NR(Guia) já cadastrado.", "numero_duplicado")

    ok = dal.create(
        """
        INSERT INTO tb_guia (
            numero, id_empresa, id_linha, id_turno, id_veiculo, id_motorista,
            id_item_map,
            hor_ini, hor_fim, roleta01_ini, roleta01_fim, roleta2_ini, roleta2_fim,
            observacao, data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dados["numero"],
            dados["id_empresa"],
            dados["id_linha"],
            dados["id_turno"],
            dados["id_veiculo"],
            dados["id_motorista"],
            dados.get("id_item_map"),
            _datetime_guia(dados["data_sql"], dados["hor_ini"]),
            _datetime_guia(dados["data_sql"], dados["hor_fim"]),
            dados["roleta01_ini"],
            dados["roleta01_fim"],
            dados["roleta2_ini"],
            dados["roleta2_fim"],
            dados["observacao"],
            _data_cadastro_agora(),
        ),
    )
    if not ok:
        return GuiaError("Falha ao salvar guia.", "persistencia")
    row = dal.read(
        "SELECT id_guia FROM tb_guia WHERE numero = ?",
        (dados["numero"],),
    )
    return _row_guia(dal, int(row.iloc[0]["id_guia"])) or {"ok": True}


def atualizar_guia(dal, id_guia: int, body: dict[str, Any]) -> dict[str, Any] | GuiaError:
    atual = dal.read("SELECT id_guia FROM tb_guia WHERE id_guia = ?", (id_guia,))
    if atual.empty:
        return GuiaError("Guia não encontrada.", "nao_encontrado")

    body_ctx = _aplicar_contexto_escala(dal, body)
    if isinstance(body_ctx, GuiaError):
        return body_ctx
    validado = _validar_payload(body_ctx)
    if isinstance(validado, GuiaError):
        return validado
    dados = _resolver_vinculos(dal, validado)
    if isinstance(dados, GuiaError):
        return dados

    dup = dal.read(
        "SELECT id_guia FROM tb_guia WHERE numero = ? AND id_guia <> ?",
        (dados["numero"], id_guia),
    )
    if not dup.empty:
        return GuiaError("NR(Guia) já cadastrado.", "numero_duplicado")

    ok = dal.update(
        """
        UPDATE tb_guia
        SET numero = ?, id_empresa = ?, id_linha = ?, id_turno = ?,
            id_veiculo = ?, id_motorista = ?, id_item_map = ?,
            hor_ini = ?, hor_fim = ?,
            roleta01_ini = ?, roleta01_fim = ?, roleta2_ini = ?, roleta2_fim = ?,
            observacao = ?
        WHERE id_guia = ?
        """,
        (
            dados["numero"],
            dados["id_empresa"],
            dados["id_linha"],
            dados["id_turno"],
            dados["id_veiculo"],
            dados["id_motorista"],
            dados.get("id_item_map"),
            _datetime_guia(dados["data_sql"], dados["hor_ini"]),
            _datetime_guia(dados["data_sql"], dados["hor_fim"]),
            dados["roleta01_ini"],
            dados["roleta01_fim"],
            dados["roleta2_ini"],
            dados["roleta2_fim"],
            dados["observacao"],
            id_guia,
        ),
    )
    if not ok:
        return GuiaError("Falha ao atualizar guia.", "persistencia")
    row = _row_guia(dal, id_guia)
    if row is None:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    return row


def excluir_guia(dal, id_guia: int) -> GuiaError | None:
    em_uso = dal.read(
        "SELECT id_cs FROM tb_chegada_saida WHERE id_gui = ? LIMIT 1",
        (id_guia,),
    )
    if not em_uso.empty:
        return GuiaError("Guia vinculada a chegada/saída; não é possível excluir.", "guia_em_uso")
    ok = dal.delete("DELETE FROM tb_guia WHERE id_guia = ?", (id_guia,))
    if not ok:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    return None
