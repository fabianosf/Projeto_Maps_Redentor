# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Contexto de escala (Mapa) para a Guia + alteração auditada."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .guia_service import GuiaError, _data_br_para_sql


def listar_escalas_guia(
    dal, data_br: str, id_mapa: Optional[int] = None
) -> dict[str, Any] | GuiaError:
    """
    Lista mapas do dia e, se id_mapa informado, só as escalas (carros) daquele mapa.
    Sem id_mapa: retorna mapas para o seletor; escalas vazias.
    """
    data_sql = _data_br_para_sql((data_br or "").strip())
    if not data_sql:
        return GuiaError("Data inválida.", "validacao")

    mapas_df = dal.read(
        """
        SELECT DISTINCT
            m.id_registro, m.cod_map, m.codigo_mapa, m.id_turno, t.descricao AS turno
        FROM tb_map m
        INNER JOIN tb_item_map i ON i.idmap = m.id_registro
        LEFT JOIN tb_turno t ON t.id_turno = m.id_turno
        WHERE m.data = ?
        ORDER BY m.codigo_mapa ASC, m.cod_map ASC
        """,
        (data_sql,),
    )
    mapas: list[dict[str, Any]] = []
    if mapas_df is not None and not getattr(mapas_df, "empty", True):
        for raw in mapas_df.to_dict(orient="records"):
            r = _safe_row(raw)
            id_map = _as_int(r.get("id_registro"))
            if id_map is None:
                continue
            cod = _as_int(r.get("cod_map"))
            codigo_mapa = str(r.get("codigo_mapa") or "").strip() or None
            rotulo = codigo_mapa or (f"Mapa {cod}" if cod is not None else "Mapa")
            turno = r.get("turno")
            mapas.append(
                {
                    "id_registro": id_map,
                    "cod_map": cod,
                    "codigo_mapa": codigo_mapa,
                    "id_turno": _as_int(r.get("id_turno")),
                    "turno": turno,
                    "data": data_br,
                    "label": f"{rotulo} · {turno or '—'}",
                }
            )

    escalas: list[dict[str, Any]] = []
    if id_mapa is not None:
        df = dal.read(
            """
            SELECT
                i.id_item, i.idmap AS id_mapa, i.status_escala,
                m.cod_map, m.codigo_mapa, m.id_turno,
                t.descricao AS turno,
                l.codigo_linha, l.descricao AS linha_descricao,
                v.numero_frota,
                mot.matricula AS matricula_motorista, mot.nome AS motorista_nome
            FROM tb_item_map i
            INNER JOIN tb_map m ON m.id_registro = i.idmap
            LEFT JOIN tb_turno t ON t.id_turno = m.id_turno
            LEFT JOIN tb_linha l ON l.id_linha = i.id_linha
            LEFT JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
            LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
            WHERE m.data = ? AND m.id_registro = ?
            ORDER BY v.numero_frota ASC, i.id_item ASC
            """,
            (data_sql, id_mapa),
        )
        if df is not None and not getattr(df, "empty", True):
            for raw in df.to_dict(orient="records"):
                r = _safe_row(raw)
                id_item = _as_int(r.get("id_item"))
                id_map = _as_int(r.get("id_mapa"))
                if id_item is None or id_map is None:
                    continue
                frota = r.get("numero_frota")
                mat = r.get("matricula_motorista")
                codigo_mapa = str(r.get("codigo_mapa") or "").strip() or None
                escalas.append(
                    {
                        "id_item": id_item,
                        "id_mapa": id_map,
                        "cod_map": _as_int(r.get("cod_map")),
                        "codigo_mapa": codigo_mapa,
                        "id_turno": _as_int(r.get("id_turno")),
                        "turno": r.get("turno"),
                        "numero_frota": frota,
                        "matricula_motorista": mat,
                        "motorista": r.get("motorista_nome"),
                        "codigo_linha": r.get("codigo_linha"),
                        "linha": r.get("linha_descricao"),
                        "status_escala": r.get("status_escala"),
                        "label": (
                            f"Carro {frota or '—'}"
                            + (f" · Mot. {mat}" if mat else "")
                        ),
                    }
                )

    return {
        "data": data_br,
        "mapas": mapas,
        "escalas": escalas,
    }


def _as_int(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _hhmm(valor: Any) -> Optional[str]:
    if valor is None or valor == "":
        return None
    import re

    m = re.search(r"(\d{2}):(\d{2})", str(valor))
    return f"{m.group(1)}:{m.group(2)}" if m else None


def _safe_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "item"):
            try:
                out[k] = v.item()
                continue
            except Exception:
                pass
        if hasattr(v, "isoformat"):
            try:
                out[k] = v.isoformat(sep=" ", timespec="seconds")
                continue
            except Exception:
                pass
        out[k] = None if v != v else v
    return out


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def obter_contexto_escala(dal, id_item: int) -> dict[str, Any] | GuiaError:
    """Dados da escala (Mapa) para preencher a Guia — somente leitura operacional."""
    df = dal.read(
        """
        SELECT
            i.id_item, i.idmap AS id_mapa, i.id_linha, i.id_veiculo, i.id_motorista,
            i.hor_ini_jor, i.hor_fim_jor, i.chegada_ponto, i.status_escala,
            m.cod_map, m.codigo_mapa, m.data AS mapa_data, m.id_turno,
            t.descricao AS turno_descricao,
            l.codigo_linha, l.descricao AS linha_descricao, l.id_empresa,
            e.descricao AS empresa_descricao,
            v.numero_frota,
            mot.matricula AS matricula_motorista, mot.nome AS motorista_nome
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        LEFT JOIN tb_turno t ON t.id_turno = m.id_turno
        LEFT JOIN tb_linha l ON l.id_linha = i.id_linha
        LEFT JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        LEFT JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (id_item,),
    )
    if df is None or getattr(df, "empty", True):
        return GuiaError("Escala não encontrada.", "nao_encontrado")

    item = _safe_row(df.iloc[0].to_dict())
    viagens_df = dal.read(
        """
        SELECT id_viagem, horario_saida, horario_chegada, placa,
               intervalo, qtd_pas_ida, qtd_pas_volta
        FROM tb_viagem
        WHERE id_item_registro = ?
        ORDER BY COALESCE(horario_saida, horario_chegada) ASC, id_viagem ASC
        """,
        (id_item,),
    )
    viagens = []
    if viagens_df is not None and not getattr(viagens_df, "empty", True):
        for row in viagens_df.to_dict(orient="records"):
            r = _safe_row(row)
            viagens.append(
                {
                    "id_viagem": _as_int(r.get("id_viagem")),
                    "horario_saida": _hhmm(r.get("horario_saida")),
                    "horario_chegada": _hhmm(r.get("horario_chegada")),
                    "placa": r.get("placa"),
                    "qtd_pas_ida": _as_int(r.get("qtd_pas_ida")),
                    "qtd_pas_volta": _as_int(r.get("qtd_pas_volta")),
                }
            )

    data_raw = item.get("mapa_data")
    data_br = None
    if data_raw is not None:
        s = str(data_raw)
        if len(s) >= 10 and s[4] == "-":
            data_br = f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        else:
            data_br = s

    return {
        "id_item": _as_int(item.get("id_item")),
        "id_mapa": _as_int(item.get("id_mapa")),
        "cod_map": _as_int(item.get("cod_map")),
        "codigo_mapa": str(item.get("codigo_mapa") or "").strip() or None,
        "data": data_br,
        "mapa_data": item.get("mapa_data"),
        "id_empresa": _as_int(item.get("id_empresa")),
        "empresa": item.get("empresa_descricao"),
        "id_linha": _as_int(item.get("id_linha")),
        "linha": item.get("linha_descricao"),
        "codigo_linha": item.get("codigo_linha"),
        "id_turno": _as_int(item.get("id_turno")),
        "turno": item.get("turno_descricao"),
        "id_veiculo": _as_int(item.get("id_veiculo")),
        "numero_frota": item.get("numero_frota"),
        "id_motorista": _as_int(item.get("id_motorista")),
        "matricula_motorista": item.get("matricula_motorista"),
        "motorista": item.get("motorista_nome"),
        "chegada_ponto": item.get("chegada_ponto"),
        "chegada_ponto_hhmm": _hhmm(item.get("chegada_ponto")),
        "hor_ini_jor": item.get("hor_ini_jor"),
        "hor_ini_jor_hhmm": _hhmm(item.get("hor_ini_jor")),
        "hor_fim_jor": item.get("hor_fim_jor"),
        "hor_fim_jor_hhmm": _hhmm(item.get("hor_fim_jor")),
        "status_escala": item.get("status_escala"),
        "viagens_previstas": viagens,
    }


def _id_veiculo_por_frota(dal, numero: str) -> Optional[int]:
    numero = (numero or "").strip()
    if not numero:
        return None
    df = dal.read(
        "SELECT id_veiculo FROM tb_veiculo WHERE ativo = 1 AND numero_frota = ? LIMIT 1",
        (numero,),
    )
    if df is None or getattr(df, "empty", True):
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
    if df is None or getattr(df, "empty", True):
        return None
    return int(df.iloc[0]["id_motorista"])


def _audit(
    dal,
    *,
    id_item: int,
    id_usuario: int,
    justificativa: str,
    campo: str,
    valor_anterior: Any,
    valor_novo: Any,
) -> None:
    dal.create(
        """
        INSERT INTO tb_escala_alteracao (
            id_item, id_usuario, justificativa, campo,
            valor_anterior, valor_novo, registrado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_item,
            id_usuario,
            justificativa,
            campo,
            None if valor_anterior is None else str(valor_anterior),
            None if valor_novo is None else str(valor_novo),
            _agora(),
        ),
    )


def registrar_alteracao_escala(
    dal,
    id_item: int,
    body: dict[str, Any],
    id_usuario: int,
) -> dict[str, Any] | GuiaError:
    """
    Altera veículo, motorista ou horários da escala com justificativa e auditoria.
    Não substitui o fluxo normal de Mapa — apenas alterações excepcionais.
    """
    justificativa = str(body.get("justificativa", "")).strip()
    if not justificativa:
        return GuiaError("Informe a justificativa da alteração de escala.", "validacao")
    if len(justificativa) > 300:
        return GuiaError("Justificativa deve ter no máximo 300 caracteres.", "validacao")

    atual = dal.read(
        """
        SELECT i.*, v.numero_frota, m.matricula AS matricula_motorista
        FROM tb_item_map i
        LEFT JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        LEFT JOIN tb_motorista m ON m.id_motorista = i.id_motorista
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (id_item,),
    )
    if atual is None or getattr(atual, "empty", True):
        return GuiaError("Escala não encontrada.", "nao_encontrado")

    row = _safe_row(atual.iloc[0].to_dict())
    if str(row.get("status_escala") or "").upper() == "ENCERRADA":
        return GuiaError("Escala encerrada não pode ser alterada.", "escala_encerrada")

    # (label_audit, coluna_sql, valor_novo_sql, valor_anterior_aud, valor_novo_aud)
    mudancas: list[tuple[str, str, Any, Any, Any]] = []

    nova_frota = body.get("numero_frota", body.get("carro"))
    if nova_frota is not None and str(nova_frota).strip() != "":
        frota = str(nova_frota).strip()
        if not frota.isdigit() or len(frota) > 5:
            return GuiaError("Carro deve conter até 5 dígitos numéricos.", "validacao")
        id_vei = _id_veiculo_por_frota(dal, frota)
        if id_vei is None:
            return GuiaError("Carro não encontrado.", "carro_invalido")
        if id_vei != _as_int(row.get("id_veiculo")):
            mudancas.append(
                ("veiculo", "id_veiculo", id_vei, str(row.get("numero_frota")), frota)
            )

    nova_mat = body.get("matricula_motorista", body.get("motorista"))
    if nova_mat is not None and str(nova_mat).strip() != "":
        mat = str(nova_mat).strip()
        if not mat.isdigit() or len(mat) > 5:
            return GuiaError("Motorista deve conter até 5 dígitos numéricos.", "validacao")
        id_mot = _id_motorista_por_matricula(dal, mat)
        if id_mot is None:
            return GuiaError("Motorista não encontrado.", "motorista_invalido")
        if id_mot != _as_int(row.get("id_motorista")):
            mudancas.append(
                (
                    "motorista",
                    "id_motorista",
                    id_mot,
                    str(row.get("matricula_motorista")),
                    mat,
                )
            )

    for campo_body, coluna, label in (
        ("hor_ini_jor", "hor_ini_jor", "hor_ini_jor"),
        ("hor_fim_jor", "hor_fim_jor", "hor_fim_jor"),
        ("chegada_ponto", "chegada_ponto", "chegada_ponto"),
    ):
        if campo_body not in body:
            continue
        novo = body.get(campo_body)
        if novo is None or str(novo).strip() == "":
            continue
        # Aceita HH:MM → concatena na data do valor atual se possível
        texto = str(novo).strip()
        if len(texto) == 5 and texto[2] == ":":
            base = str(row.get(coluna) or _agora())[:10]
            if len(base) >= 10 and base[4] == "-":
                texto = f"{base} {texto}:00"
            else:
                # data BR do mapa
                texto = f"{_agora()[:10]} {texto}:00"
        ant = row.get(coluna)
        if str(ant) != str(texto):
            mudancas.append((label, coluna, texto, ant, texto))

    if not mudancas:
        return GuiaError("Nenhuma alteração informada.", "validacao")

    sets = []
    vals: list[Any] = []
    for _label, coluna, novo, _ant, _novo_aud in mudancas:
        sets.append(f"{coluna} = ?")
        vals.append(novo)
    vals.append(id_item)
    ok = dal.update(
        f"UPDATE tb_item_map SET {', '.join(sets)} WHERE id_item = ?",
        tuple(vals),
    )
    if not ok:
        return GuiaError("Falha ao alterar escala.", "persistencia")

    for label, _coluna, _novo, ant, novo_aud in mudancas:
        _audit(
            dal,
            id_item=id_item,
            id_usuario=id_usuario,
            justificativa=justificativa,
            campo=label,
            valor_anterior=ant,
            valor_novo=novo_aud,
        )

    return obter_contexto_escala(dal, id_item)
