# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Consolidação Guia = visão de Mapa + Viagens + Roleta (sem duplicar dados)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from .guia_service import GuiaError, _data_br_para_sql, listar_guias

_AJUSTE_RE = re.compile(
    r"\[AM\s+(ida|volta)=(\d+)\s+(\d{2}:\d{2})\]\s*(.*?)(?=\n\[AM\s+|$)",
    re.IGNORECASE | re.DOTALL,
)


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
    m = re.search(r"(\d{2}):(\d{2})", str(valor))
    return f"{m.group(1)}:{m.group(2)}" if m else None


def _calc_embarques(ini: Any, fim: Any) -> Optional[int]:
    a = _as_int(ini)
    b = _as_int(fim)
    if a is None or b is None:
        return None
    d = b - a
    return d if d >= 0 else None


def _roleta_parcial(ini: Any, fim: Any) -> bool:
    has_ini = _as_int(ini) is not None
    has_fim = _as_int(fim) is not None
    return (has_ini and not has_fim) or (not has_ini and has_fim)


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
        out[k] = None if v != v else v  # NaN check
    return out


def _parse_ajustes(observacao: Optional[str]) -> dict[str, dict[str, Any]]:
    """Extrai ajustes manuais da observação sem alterar roleta original."""
    texto = observacao or ""
    achados: dict[str, dict[str, Any]] = {}
    for m in _AJUSTE_RE.finditer(texto):
        sentido = m.group(1).lower()
        achados[sentido] = {
            "embarques": int(m.group(2)),
            "em": m.group(3),
            "justificativa": (m.group(4) or "").strip(),
        }
    return achados


def _strip_ajustes(observacao: Optional[str]) -> str:
    texto = observacao or ""
    limpo = _AJUSTE_RE.sub("", texto)
    return re.sub(r"\n{2,}", "\n", limpo).strip()


def montar_observacao_com_ajuste(
    observacao_atual: Optional[str],
    sentido: str,
    embarques: int,
    justificativa: str,
    agora: Optional[datetime] = None,
    max_len: int = 150,
) -> str:
    agora = agora or datetime.now()
    hhmm = agora.strftime("%H:%M")
    base = _strip_ajustes(observacao_atual)
    outros = _parse_ajustes(observacao_atual)
    outros[sentido] = {
        "embarques": embarques,
        "em": hhmm,
        "justificativa": justificativa.strip(),
    }
    blocos = []
    for s in ("ida", "volta"):
        if s not in outros:
            continue
        a = outros[s]
        just = str(a.get("justificativa") or "").strip()
        blocos.append(f"[AM {s}={int(a['embarques'])} {a['em']}]{just}")
    merged = "\n".join(x for x in [base, *blocos] if x)
    return merged[:max_len]


def _status_viagem(
    *,
    embarques_roleta: Optional[int],
    parcial: bool,
    ajuste: Optional[dict[str, Any]],
    divergente: bool,
    falha_leitura: bool,
    atualizando: bool,
) -> str:
    if falha_leitura:
        return "falha"
    if atualizando:
        return "atualizando"
    if ajuste is not None:
        return "manual"
    if divergente:
        return "divergencia"
    if parcial or embarques_roleta is None:
        return "pendente"
    return "sincronizado"


def _pior_status(statuses: list[str]) -> str:
    ordem = [
        "falha",
        "divergencia",
        "manual",
        "pendente",
        "atualizando",
        "sincronizado",
    ]
    for s in ordem:
        if s in statuses:
            return s
    return "sincronizado"


def _carregar_viagens_mapa(dal, data_sql: str) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT
            v.id_viagem,
            v.id_item_registro,
            v.horario_saida,
            v.horario_chegada,
            v.placa,
            v.qtd_pas_ida,
            v.qtd_pas_volta,
            i.id_veiculo,
            i.id_linha,
            i.id_motorista,
            i.fim_real,
            i.status_escala,
            m.id_registro AS id_mapa,
            m.cod_map,
            m.codigo_mapa,
            m.id_turno,
            m.data AS mapa_data,
            ve.numero_frota,
            mot.matricula AS matricula_motorista,
            mot.nome AS motorista_nome,
            t.descricao AS turno_descricao,
            l.codigo_linha AS linha_codigo,
            l.descricao AS linha_descricao
        FROM tb_viagem v
        INNER JOIN tb_item_map i ON i.id_item = v.id_item_registro
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        LEFT JOIN tb_veiculo ve ON ve.id_veiculo = i.id_veiculo
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        LEFT JOIN tb_turno t ON t.id_turno = m.id_turno
        LEFT JOIN tb_linha l ON l.id_linha = i.id_linha
        WHERE DATE(m.data) = ?
        ORDER BY COALESCE(v.horario_saida, v.horario_chegada) ASC, v.id_viagem ASC
        """,
        (data_sql,),
    )
    if df is None or getattr(df, "empty", True):
        return []
    return [_safe_row(r) for r in df.to_dict(orient="records")]


def _leituras_cs_por_guia(dal, data_sql: str) -> dict[int, dict[str, Any]]:
    """Min/max de roleta_01/02 em chegada/saída do dia, por id_guia."""
    df = dal.read(
        """
        SELECT
            cs.id_gui AS id_guia,
            MIN(cs.roleta_01) AS roleta01_min,
            MAX(cs.roleta_01) AS roleta01_max,
            MIN(cs.roleta_02) AS roleta02_min,
            MAX(cs.roleta_02) AS roleta02_max,
            MAX(cs.horario) AS ultima_horario
        FROM tb_chegada_saida cs
        INNER JOIN tb_guia g ON g.id_guia = cs.id_gui
        WHERE cs.id_gui IS NOT NULL
          AND DATE(COALESCE(g.hor_ini, g.hor_fim, g.data)) = ?
        GROUP BY cs.id_gui
        """,
        (data_sql,),
    )
    if df is None or getattr(df, "empty", True):
        return {}
    out: dict[int, dict[str, Any]] = {}
    for row in df.to_dict(orient="records"):
        r = _safe_row(row)
        gid = _as_int(r.get("id_guia"))
        if gid is None:
            continue
        out[gid] = r
    return out


def _escolher_roleta(
    guia: Optional[dict[str, Any]],
    cs: Optional[dict[str, Any]],
    sentido: str,
) -> tuple[Optional[int], Optional[int], str]:
    """
    Prioriza leituras de roleta na guia; completa com chegada/saída se parcial/ausente.
    Retorna (ini, fim, fonte) fonte in roleta|chegada_saida|mista|nenhuma
    """
    if sentido == "ida":
        g_ini = guia.get("roleta01_ini") if guia else None
        g_fim = guia.get("roleta01_fim") if guia else None
        c_ini = cs.get("roleta01_min") if cs else None
        c_fim = cs.get("roleta01_max") if cs else None
    else:
        g_ini = guia.get("roleta2_ini") if guia else None
        g_fim = guia.get("roleta2_fim") if guia else None
        c_ini = cs.get("roleta02_min") if cs else None
        c_fim = cs.get("roleta02_max") if cs else None

    ini = _as_int(g_ini)
    fim = _as_int(g_fim)
    fonte = "nenhuma"
    if ini is not None or fim is not None:
        fonte = "roleta"
    if ini is None and _as_int(c_ini) is not None:
        ini = _as_int(c_ini)
        fonte = "mista" if fonte == "roleta" else "chegada_saida"
    if fim is None and _as_int(c_fim) is not None:
        fim = _as_int(c_fim)
        fonte = "mista" if fonte in ("roleta", "mista") else "chegada_saida"
    # Se só CS e min==max (uma leitura), não inventa par.
    if fonte == "chegada_saida" and ini is not None and fim is not None and ini == fim:
        return ini, None, fonte
    return ini, fim, fonte


def _match_guia(
    guias: list[dict[str, Any]],
    *,
    id_veiculo: Optional[int],
    id_linha: Optional[int],
    id_turno: Optional[int],
) -> Optional[dict[str, Any]]:
    candidatos = guias
    if id_veiculo is not None:
        candidatos = [
            g for g in candidatos if _as_int(g.get("id_veiculo")) == id_veiculo
        ]
    if id_linha is not None:
        filtrado = [g for g in candidatos if _as_int(g.get("id_linha")) == id_linha]
        if filtrado:
            candidatos = filtrado
    if id_turno is not None:
        filtrado = [g for g in candidatos if _as_int(g.get("id_turno")) == id_turno]
        if filtrado:
            candidatos = filtrado
    return candidatos[0] if candidatos else None


def _indexar_leituras_dia(dal, data_sql: str) -> dict[tuple[Any, ...], dict[str, Any]]:
    df = dal.read(
        """
        SELECT r.*, u.matricula AS matricula_usuario, u.nome AS nome_usuario
        FROM tb_guia_roleta_leitura r
        LEFT JOIN tb_usuario u ON u.id_usuario = r.id_usuario
        LEFT JOIN tb_viagem v ON v.id_viagem = r.id_viagem
        LEFT JOIN tb_item_map i ON i.id_item = v.id_item_registro
        LEFT JOIN tb_map m ON m.id_registro = i.idmap
        LEFT JOIN tb_guia g ON g.id_guia = r.id_guia
        WHERE (m.data IS NOT NULL AND DATE(m.data) = ?)
           OR (g.id_guia IS NOT NULL AND DATE(COALESCE(g.hor_ini, g.hor_fim, g.data)) = ?)
           OR (r.id_viagem IS NULL AND r.id_guia IS NULL)
        """,
        (data_sql, data_sql),
    )
    idx: dict[tuple[Any, ...], dict[str, Any]] = {}
    if df is None or getattr(df, "empty", True):
        return idx
    for row in df.to_dict(orient="records"):
        r = _safe_row(row)
        sentido = str(r.get("sentido") or "").lower()
        fonte = str(r.get("fonte") or "").lower()
        id_viagem = _as_int(r.get("id_viagem"))
        id_guia = _as_int(r.get("id_guia"))
        if id_viagem is not None:
            idx[(id_viagem, sentido, fonte, "v")] = r
        if id_guia is not None and id_viagem is None:
            idx[(id_guia, sentido, fonte, "g")] = r
    return idx


def _montar_card(
    dal,
    *,
    seq: int,
    sentido: str,
    viagem: Optional[dict[str, Any]],
    guia: Optional[dict[str, Any]],
    data_br: str,
    cs_map: dict[int, dict[str, Any]],
    leituras_idx: dict[tuple[Any, ...], dict[str, Any]],
) -> dict[str, Any]:
    from .guia_roleta_service import bloco_fonte, sugerir_leitura_inicial

    gid = _as_int(guia.get("id_guia")) if guia else None
    id_viagem = _as_int(viagem.get("id_viagem")) if viagem else None
    cs = cs_map.get(gid) if gid is not None else None
    ini, fim, fonte_roleta = _escolher_roleta(guia, cs, sentido)
    embarques_roleta = _calc_embarques(ini, fim)
    parcial = _roleta_parcial(ini, fim)
    falha = (
        _as_int(ini) is not None
        and _as_int(fim) is not None
        and _as_int(fim) < _as_int(ini)  # type: ignore[operator]
    )

    ajustes = _parse_ajustes(guia.get("observacao") if guia else None)
    ajuste = ajustes.get(sentido)

    previsto = None
    if viagem is not None:
        previsto = _as_int(
            viagem.get("qtd_pas_ida") if sentido == "ida" else viagem.get("qtd_pas_volta")
        )

    id_veiculo = (
        _as_int(viagem.get("id_veiculo"))
        if viagem
        else (_as_int(guia.get("id_veiculo")) if guia else None)
    )

    def _peg(fonte: str) -> Optional[dict[str, Any]]:
        if id_viagem is not None:
            hit = leituras_idx.get((id_viagem, sentido, fonte, "v"))
            if hit:
                return hit
        if gid is not None:
            return leituras_idx.get((gid, sentido, fonte, "g"))
        return None

    jae = bloco_fonte(_peg("jae"))
    riocard = bloco_fonte(_peg("riocard"))
    if id_veiculo is not None:
        if jae.get("leitura_ini") is None:
            jae["sugestao_ini"] = sugerir_leitura_inicial(
                dal, id_veiculo=id_veiculo, fonte="jae", sentido=sentido
            )
        if riocard.get("leitura_ini") is None:
            riocard["sugestao_ini"] = sugerir_leitura_inicial(
                dal, id_veiculo=id_veiculo, fonte="riocard", sentido=sentido
            )

    divergente = False
    if (
        embarques_roleta is not None
        and previsto is not None
        and embarques_roleta != previsto
        and ajuste is None
    ):
        divergente = True

    atualizando = False
    if viagem is not None:
        status_escala = str(viagem.get("status_escala") or "").upper()
        atualizando = status_escala == "EM_ANDAMENTO" and viagem.get("fim_real") in (
            None,
            "",
        )

    statuses_fonte: list[str] = []
    for bloco in (jae, riocard):
        st = bloco.get("status_leitura")
        if st == "iniciada":
            statuses_fonte.append("pendente")
        elif st == "finalizada" and bloco.get("virada"):
            statuses_fonte.append("manual")
        elif st == "finalizada":
            statuses_fonte.append("sincronizado")

    if statuses_fonte:
        status = _pior_status(statuses_fonte)
        if atualizando and "pendente" in statuses_fonte:
            status = "atualizando"
        origem = "manual" if status == "manual" else "roleta"
        embarques = 0
    elif ajuste is not None:
        embarques = int(ajuste["embarques"])
        origem = "manual"
        status = _status_viagem(
            embarques_roleta=embarques_roleta,
            parcial=parcial,
            ajuste=ajuste,
            divergente=divergente,
            falha_leitura=bool(falha),
            atualizando=False,
        )
    elif embarques_roleta is not None:
        embarques = embarques_roleta
        origem = "roleta"
        status = _status_viagem(
            embarques_roleta=embarques_roleta,
            parcial=parcial,
            ajuste=ajuste,
            divergente=divergente,
            falha_leitura=bool(falha),
            atualizando=atualizando and embarques_roleta is None,
        )
    elif previsto is not None:
        embarques = previsto
        origem = "mapa"
        status = "pendente"
    else:
        embarques = 0
        origem = "roleta"
        status = "atualizando" if atualizando else "pendente"

    horario = None
    horario_saida = None
    horario_chegada = None
    if viagem is not None:
        horario_saida = _hhmm(viagem.get("horario_saida"))
        horario_chegada = _hhmm(viagem.get("horario_chegada"))
        horario = horario_saida or horario_chegada or _hhmm(viagem.get("placa"))
    if not horario and guia is not None:
        horario = _hhmm(guia.get("hor_ini")) or _hhmm(guia.get("hor_fim"))

    veiculo = ""
    if viagem is not None:
        veiculo = str(viagem.get("numero_frota") or "").strip()
    if not veiculo and guia is not None:
        veiculo = str(guia.get("numero_frota") or "").strip()

    cod_map = _as_int(viagem.get("cod_map")) if viagem else None
    codigo_mapa = None
    if viagem is not None:
        codigo_mapa = str(viagem.get("codigo_mapa") or "").strip() or None
    linha_cod = None
    if viagem is not None:
        linha_cod = viagem.get("linha_codigo")
    elif guia is not None:
        linha_cod = guia.get("linha_codigo")

    turno = None
    if viagem is not None:
        turno = viagem.get("turno_descricao")
    elif guia is not None:
        turno = guia.get("turno_descricao")

    key = f"v-{id_viagem or gid or seq}-{sentido}"

    responsavel = None
    for bloco in (jae, riocard):
        if bloco and bloco.get("nome_usuario"):
            responsavel = bloco.get("nome_usuario")
            break

    obs_guia = _strip_ajustes(guia.get("observacao") if guia else None) or None
    motorista_nome = viagem.get("motorista_nome") if viagem else None
    matricula_mot = viagem.get("matricula_motorista") if viagem else None
    if guia and not matricula_mot:
        matricula_mot = guia.get("matricula_motorista")

    if codigo_mapa:
        mapa_label = codigo_mapa
    elif cod_map is not None:
        mapa_label = f"Mapa {str(cod_map).zfill(3)}"
    elif linha_cod is not None and str(linha_cod).isdigit():
        mapa_label = f"Mapa {str(linha_cod).zfill(3)}"
    elif guia:
        mapa_label = f"Guia {guia.get('numero')}"
    else:
        mapa_label = None

    linha_label = None
    if linha_cod is not None and str(linha_cod).strip():
        linha_label = str(linha_cod).strip()
    elif guia is not None and guia.get("linha_descricao"):
        linha_label = str(guia.get("linha_descricao")).strip() or None

    return {
        "key": key,
        "viagem_label": f"Viagem {seq:02d}",
        "id_viagem": id_viagem,
        "id_guia": gid,
        "id_trecho": None,
        "trecho_status": None,
        "trecho_versao": None,
        "id_mapa": _as_int(viagem.get("id_mapa")) if viagem else None,
        "cod_map": cod_map,
        "codigo_mapa": codigo_mapa,
        "mapa": mapa_label,
        "linha": linha_label,
        "codigo_linha": linha_cod,
        "veiculo": veiculo or "—",
        "numero_frota": veiculo or None,
        "id_veiculo": id_veiculo,
        "motorista": motorista_nome,
        "matricula_motorista": matricula_mot,
        "responsavel": responsavel,
        "ocorrencias": obs_guia,
        "observacao": obs_guia,
        "data": data_br,
        "turno": turno,
        "sentido": sentido,
        "horario": horario or "—",
        "horario_saida": horario_saida,
        "horario_chegada": horario_chegada,
        "embarques": embarques,
        "embarques_roleta": embarques_roleta,
        "embarques_previsto_mapa": previsto,
        "origem": origem,
        "status": status,
        "roleta": {
            "ini": ini,
            "fim": fim,
            "fonte": fonte_roleta,
        },
        "ajuste": ajuste,
        "jae": jae,
        "riocard": riocard,
    }


def consultar_guia_consolidada(
    dal,
    data_br: Optional[str] = None,
    *,
    sentido: Optional[str] = None,
    origem: Optional[str] = None,
    status: Optional[str] = None,
    id_turno: Optional[int] = None,
    id_linha: Optional[int] = None,
    somente_pendencias: bool = False,
) -> dict[str, Any] | GuiaError:
    """
    Visão consolidada do dia: Mapa/Viagens + Roleta (tb_guia / chegada-saída).
    Não grava nem duplica dados — apenas agrega leituras existentes.
    """
    data_br = (data_br or "").strip() or datetime.now().strftime("%d/%m/%Y")
    data_sql = _data_br_para_sql(data_br)
    if not data_sql:
        return GuiaError("Data inválida.", "validacao")

    sentido_f = (sentido or "").strip().lower() or None
    if sentido_f and sentido_f not in ("ida", "volta"):
        return GuiaError("Filtro sentido inválido.", "validacao")
    origem_f = (origem or "").strip().lower() or None
    if origem_f and origem_f not in ("roleta", "manual", "mapa"):
        return GuiaError("Filtro origem inválido.", "validacao")
    status_f = (status or "").strip().lower() or None
    status_ok = {
        "sincronizado",
        "atualizando",
        "pendente",
        "divergencia",
        "falha",
        "manual",
    }
    if status_f and status_f not in status_ok:
        return GuiaError("Filtro status inválido.", "validacao")

    guias_raw = listar_guias(dal, data_br)
    if isinstance(guias_raw, GuiaError):
        return guias_raw
    guias = [_safe_row(g) for g in guias_raw]

    try:
        viagens_mapa = _carregar_viagens_mapa(dal, data_sql)
        cs_map = _leituras_cs_por_guia(dal, data_sql)
        leituras_idx = _indexar_leituras_dia(dal, data_sql)
    except Exception:
        return {
            "data": data_br,
            "status": "falha",
            "resumo": {
                "titulo_mapa": "Guia do dia",
                "turno": None,
                "cod_map": None,
                "codigo_mapa": None,
                "id_registro": None,
                "embarques_ida": 0,
                "embarques_volta": 0,
                "ida": {"jae": 0, "riocard": 0},
                "volta": {"jae": 0, "riocard": 0},
                "total_viagens": 0,
                "total_pendente": 0,
                "ultima_leitura": None,
            },
            "viagens": [],
            "guias": guias,
            "erro_integracao": "Falha ao consolidar Mapa/Viagens/Roleta.",
        }

    cards: list[dict[str, Any]] = []
    seq = 0
    guias_usadas: set[int] = set()

    for viagem in viagens_mapa:
        if id_turno is not None and _as_int(viagem.get("id_turno")) != id_turno:
            continue
        if id_linha is not None and _as_int(viagem.get("id_linha")) != id_linha:
            continue
        guia = _match_guia(
            guias,
            id_veiculo=_as_int(viagem.get("id_veiculo")),
            id_linha=_as_int(viagem.get("id_linha")),
            id_turno=_as_int(viagem.get("id_turno")),
        )
        if guia and _as_int(guia.get("id_guia")) is not None:
            guias_usadas.add(int(guia["id_guia"]))

        for sent in ("ida", "volta"):
            seq += 1
            cards.append(
                _montar_card(
                    dal,
                    seq=seq,
                    sentido=sent,
                    viagem=viagem,
                    guia=guia,
                    data_br=data_br,
                    cs_map=cs_map,
                    leituras_idx=leituras_idx,
                )
            )

    # Guias do dia sem viagem de mapa correspondente (não perde dado operacional).
    for guia in guias:
        gid = _as_int(guia.get("id_guia"))
        if gid is not None and gid in guias_usadas:
            continue
        if id_turno is not None and _as_int(guia.get("id_turno")) != id_turno:
            continue
        if id_linha is not None and _as_int(guia.get("id_linha")) != id_linha:
            continue
        for sent in ("ida", "volta"):
            ini, fim, _fonte = _escolher_roleta(guia, cs_map.get(gid or -1), sent)
            tem_jae = leituras_idx.get((gid, sent, "jae", "g")) if gid else None
            tem_rio = leituras_idx.get((gid, sent, "riocard", "g")) if gid else None
            tem_dado = (
                _calc_embarques(ini, fim) is not None
                or _roleta_parcial(ini, fim)
                or _parse_ajustes(guia.get("observacao")).get(sent) is not None
                or tem_jae is not None
                or tem_rio is not None
            )
            if sent == "volta" and not tem_dado:
                continue
            seq += 1
            cards.append(
                _montar_card(
                    dal,
                    seq=seq,
                    sentido=sent,
                    viagem=None,
                    guia=guia,
                    data_br=data_br,
                    cs_map=cs_map,
                    leituras_idx=leituras_idx,
                )
            )

    # Re-sequencia rótulos após filtros
    filtrados: list[dict[str, Any]] = []
    for c in cards:
        if sentido_f and c["sentido"] != sentido_f:
            continue
        if origem_f and c["origem"] != origem_f:
            continue
        if status_f and c["status"] != status_f:
            continue
        if somente_pendencias and c["status"] in ("sincronizado",):
            continue
        filtrados.append(c)

    for i, c in enumerate(filtrados, start=1):
        c["viagem_label"] = f"Viagem {i:02d}"

    # Enriquece cards com trecho da jornada (quando tabela existir).
    ids_guia = sorted(
        {
            int(c["id_guia"])
            for c in filtrados
            if _as_int(c.get("id_guia")) is not None
        }
    )
    trechos_por_guia: dict[int, list[dict[str, Any]]] = {}
    if ids_guia:
        try:
            placeholders = ",".join(["?"] * len(ids_guia))
            df_t = dal.read(
                f"""
                SELECT id_trecho, id_guia, sentido, status, versao, seq,
                       id_linha, id_veiculo, hor_ini, hor_fim
                FROM tb_guia_trecho
                WHERE id_guia IN ({placeholders})
                ORDER BY seq ASC, id_trecho ASC
                """,
                tuple(ids_guia),
            )
            if df_t is not None and not getattr(df_t, "empty", True):
                for row in df_t.to_dict(orient="records"):
                    gid_t = _as_int(row.get("id_guia"))
                    if gid_t is None:
                        continue
                    trechos_por_guia.setdefault(gid_t, []).append(_safe_row(row))
        except Exception:
            trechos_por_guia = {}

    def _match_trecho(card: dict[str, Any]) -> dict[str, Any] | None:
        gid_c = _as_int(card.get("id_guia"))
        if gid_c is None:
            return None
        sent = str(card.get("sentido") or "").strip().upper()
        candidatos = [
            t
            for t in trechos_por_guia.get(gid_c, [])
            if str(t.get("sentido") or "").strip().upper() == sent
        ]
        if not candidatos:
            candidatos = list(trechos_por_guia.get(gid_c, []))
        if not candidatos:
            return None
        # Preferência: EM_TRANSITO > PLANEJADO > demais (último seq).
        ordem = {"EM_TRANSITO": 0, "PLANEJADO": 1, "CONCLUIDO": 2, "CANCELADO": 3}
        candidatos.sort(
            key=lambda t: (
                ordem.get(str(t.get("status") or "").upper(), 9),
                -int(t.get("seq") or 0),
                -int(t.get("id_trecho") or 0),
            )
        )
        return candidatos[0]

    total_pendente = 0
    for c in filtrados:
        tmatch = _match_trecho(c)
        if tmatch:
            c["id_trecho"] = _as_int(tmatch.get("id_trecho"))
            c["trecho_status"] = str(tmatch.get("status") or "").upper() or None
            c["trecho_versao"] = _as_int(tmatch.get("versao"))
            st = str(c["trecho_status"] or "")
            if st in ("PLANEJADO", "EM_TRANSITO"):
                total_pendente += 1
            continue
        # Sem trecho: pendente se não há leitura finalizada.
        jae_b = c.get("jae") or {}
        rio_b = c.get("riocard") or {}
        jae_ok = (
            jae_b.get("status_leitura") == "finalizada"
            or (
                jae_b.get("leitura_ini") is not None
                and jae_b.get("leitura_fim") is not None
            )
        )
        rio_ok = (
            rio_b.get("status_leitura") == "finalizada"
            or (
                rio_b.get("leitura_ini") is not None
                and rio_b.get("leitura_fim") is not None
            )
        )
        tem_leitura = bool(jae_b) or bool(rio_b)
        if not tem_leitura or not (jae_ok or rio_ok):
            total_pendente += 1

    emb_ida_jae = 0
    emb_ida_rio = 0
    emb_volta_jae = 0
    emb_volta_rio = 0
    for c in filtrados:
        jae_p = _as_int((c.get("jae") or {}).get("passageiros")) or 0
        rio_p = _as_int((c.get("riocard") or {}).get("passageiros")) or 0
        if c["sentido"] == "ida":
            emb_ida_jae += jae_p
            emb_ida_rio += rio_p
        else:
            emb_volta_jae += jae_p
            emb_volta_rio += rio_p

    ultima = None
    for c in filtrados:
        for h in (c.get("horario_chegada"), c.get("horario_saida"), c.get("horario")):
            hh = _hhmm(h)
            if hh and (ultima is None or hh > ultima):
                ultima = hh
        for bloco in (c.get("jae") or {}, c.get("riocard") or {}):
            hh = _hhmm(bloco.get("atualizado_em"))
            if hh and (ultima is None or hh > ultima):
                ultima = hh
    for g in guias:
        for h in (g.get("hor_fim"), g.get("hor_ini")):
            hh = _hhmm(h)
            if hh and (ultima is None or hh > ultima):
                ultima = hh
    for cs in cs_map.values():
        hh = _hhmm(cs.get("ultima_horario"))
        if hh and (ultima is None or hh > ultima):
            ultima = hh

    status_geral = _pior_status([c["status"] for c in filtrados]) if filtrados else "sincronizado"

    first = filtrados[0] if filtrados else None
    titulo = (first or {}).get("mapa") or "Guia do dia"
    turno_label = (first or {}).get("turno")
    if turno_label and "turno" not in str(turno_label).lower():
        turno_label = f"Turno {turno_label}"

    return {
        "data": data_br,
        "status": status_geral,
        "resumo": {
            "titulo_mapa": titulo,
            "turno": turno_label,
            "cod_map": (first or {}).get("cod_map"),
            "codigo_mapa": (first or {}).get("codigo_mapa"),
            "id_registro": (first or {}).get("id_mapa"),
            # Separados — não somar Ja E + RioCard.
            "ida": {"jae": emb_ida_jae, "riocard": emb_ida_rio},
            "volta": {"jae": emb_volta_jae, "riocard": emb_volta_rio},
            # Legado (compat): não agrega fontes distintas.
            "embarques_ida": emb_ida_jae,
            "embarques_volta": emb_volta_jae,
            "total_viagens": len(filtrados),
            "total_pendente": total_pendente,
            "ultima_leitura": ultima,
        },
        "viagens": filtrados,
        "guias": guias,
    }


def registrar_ajuste_manual(
    dal,
    id_guia: int,
    *,
    sentido: str,
    embarques: Any,
    justificativa: str,
) -> dict[str, Any] | GuiaError:
    """
    Registra ajuste manual com auditoria.
    Não sobrescreve roleta_* (valor original da catraca permanece).
    """
    sentido = (sentido or "").strip().lower()
    if sentido not in ("ida", "volta"):
        return GuiaError("Sentido inválido (ida|volta).", "validacao")
    emb = _as_int(embarques)
    if emb is None or emb < 0:
        return GuiaError("Informe os embarques do ajuste.", "validacao")
    just = (justificativa or "").strip()
    if not just:
        return GuiaError("Informe a justificativa do ajuste manual.", "validacao")

    from .guia_service import _row_guia

    atual = _row_guia(dal, id_guia)
    if atual is None:
        return GuiaError("Guia não encontrada.", "nao_encontrado")

    nova_obs = montar_observacao_com_ajuste(
        atual.get("observacao"),
        sentido,
        emb,
        just,
    )
    ok = dal.update(
        "UPDATE tb_guia SET observacao = ? WHERE id_guia = ?",
        (nova_obs, id_guia),
    )
    if not ok:
        return GuiaError("Falha ao registrar ajuste.", "persistencia")
    row = _row_guia(dal, id_guia)
    if row is None:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    # Garante que roleta original não foi alterada.
    for campo in ("roleta01_ini", "roleta01_fim", "roleta2_ini", "roleta2_fim"):
        if _as_int(atual.get(campo)) != _as_int(row.get(campo)):
            return GuiaError("Ajuste alterou roleta original.", "integridade")
    return row
