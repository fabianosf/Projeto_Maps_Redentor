# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Leituras manuais Ja E / RioCard por viagem (Guia)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .guia_service import GuiaError

FONTES = frozenset({"jae", "riocard"})
SENTIDOS = frozenset({"ida", "volta"})
# Contador típico 6 dígitos ao virar (reinício).
_WRAP = 1_000_000


def _as_int(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def calcular_passageiros(
    leitura_ini: Optional[int],
    leitura_fim: Optional[int],
    *,
    virada: bool,
) -> Optional[int]:
    if leitura_ini is None or leitura_fim is None:
        return None
    if leitura_fim >= leitura_ini:
        return leitura_fim - leitura_ini
    if not virada:
        return None
    return (_WRAP - leitura_ini) + leitura_fim


def sugerir_leitura_inicial(
    dal,
    *,
    id_veiculo: int,
    fonte: str,
    sentido: str,
    excluir_id_leitura: Optional[int] = None,
    id_guia: Optional[int] = None,
    id_trecho: Optional[int] = None,
) -> Optional[int]:
    """
    Sugere leitura inicial:
    1) Preferência: fim do trecho anterior da mesma Guia com o mesmo carro.
    2) Fallback: última leitura_fim do mesmo veículo/fonte/sentido.
    Se o carro mudou em relação ao trecho anterior da guia, não sugere (None).
    """
    fonte = (fonte or "").strip().lower()
    sentido = (sentido or "").strip().lower()
    if fonte not in FONTES or sentido not in SENTIDOS:
        return None

    if id_guia is not None:
        # Detecta troca de carro vs trecho anterior
        trechos = dal.read(
            """
            SELECT id_trecho, id_veiculo, jae_fim, riocard_fim, status
            FROM tb_guia_trecho
            WHERE id_guia = ?
            ORDER BY seq ASC, id_trecho ASC
            """,
            (int(id_guia),),
        )
        if trechos is not None and not getattr(trechos, "empty", True):
            rows = trechos.to_dict(orient="records")
            prev = None
            for r in rows:
                if id_trecho is not None and int(r["id_trecho"]) == int(id_trecho):
                    break
                prev = r
            if prev is not None:
                prev_vei = _as_int(prev.get("id_veiculo"))
                if prev_vei is not None and int(prev_vei) != int(id_veiculo):
                    return None  # troca de carro: exige nova leitura
                if fonte == "jae":
                    fim_t = _as_int(prev.get("jae_fim"))
                    if fim_t is not None:
                        return fim_t
                if fonte == "riocard":
                    fim_t = _as_int(prev.get("riocard_fim"))
                    if fim_t is not None:
                        return fim_t

    params: list[Any] = [id_veiculo, fonte, sentido]
    extra = ""
    if excluir_id_leitura is not None:
        extra = " AND id_leitura <> ?"
        params.append(excluir_id_leitura)
    if id_guia is not None:
        extra += " AND id_guia = ?"
        params.append(int(id_guia))
    df = dal.read(
        f"""
        SELECT leitura_fim
        FROM tb_guia_roleta_leitura
        WHERE id_veiculo = ?
          AND fonte = ?
          AND sentido = ?
          AND leitura_fim IS NOT NULL
          {extra}
        ORDER BY atualizado_em DESC, id_leitura DESC
        LIMIT 1
        """,
        tuple(params),
    )
    if df is None or getattr(df, "empty", True):
        # Sem restrição de guia — fallback global do veículo
        if id_guia is not None:
            return sugerir_leitura_inicial(
                dal,
                id_veiculo=id_veiculo,
                fonte=fonte,
                sentido=sentido,
                excluir_id_leitura=excluir_id_leitura,
                id_guia=None,
                id_trecho=None,
            )
        return None
    return _as_int(df.iloc[0]["leitura_fim"])


def _row_leitura(dal, id_leitura: int) -> Optional[dict[str, Any]]:
    df = dal.read(
        """
        SELECT r.*, u.matricula AS matricula_usuario, u.nome AS nome_usuario
        FROM tb_guia_roleta_leitura r
        LEFT JOIN tb_usuario u ON u.id_usuario = r.id_usuario
        WHERE r.id_leitura = ?
        """,
        (id_leitura,),
    )
    if df is None or getattr(df, "empty", True):
        return None
    return _safe_row(df.iloc[0].to_dict())


def _registrar_historico(
    dal,
    *,
    id_leitura: int,
    acao: str,
    leitura_ini: Optional[int],
    leitura_fim: Optional[int],
    passageiros: Optional[int],
    virada: int,
    justificativa: Optional[str],
    id_usuario: int,
) -> None:
    dal.create(
        """
        INSERT INTO tb_guia_roleta_historico (
            id_leitura, acao, leitura_ini, leitura_fim, passageiros,
            virada, justificativa, id_usuario, registrado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_leitura,
            acao,
            leitura_ini,
            leitura_fim,
            passageiros,
            virada,
            (justificativa or None),
            id_usuario,
            _agora(),
        ),
    )


def _buscar_existente(
    dal,
    *,
    id_viagem: Optional[int],
    id_guia: Optional[int],
    sentido: str,
    fonte: str,
) -> Optional[dict[str, Any]]:
    if id_viagem is not None:
        df = dal.read(
            """
            SELECT * FROM tb_guia_roleta_leitura
            WHERE id_viagem = ? AND sentido = ? AND fonte = ?
            LIMIT 1
            """,
            (id_viagem, sentido, fonte),
        )
    elif id_guia is not None:
        df = dal.read(
            """
            SELECT * FROM tb_guia_roleta_leitura
            WHERE id_guia = ? AND id_viagem IS NULL AND sentido = ? AND fonte = ?
            LIMIT 1
            """,
            (id_guia, sentido, fonte),
        )
    else:
        return None
    if df is None or getattr(df, "empty", True):
        return None
    return _safe_row(df.iloc[0].to_dict())


def _resolver_veiculo(
    dal,
    *,
    id_veiculo: Optional[int],
    id_viagem: Optional[int],
    id_guia: Optional[int],
) -> Optional[int]:
    if id_veiculo is not None and id_veiculo > 0:
        return id_veiculo
    if id_viagem is not None:
        df = dal.read(
            """
            SELECT i.id_veiculo
            FROM tb_viagem v
            INNER JOIN tb_item_map i ON i.id_item = v.id_item_registro
            WHERE v.id_viagem = ?
            LIMIT 1
            """,
            (id_viagem,),
        )
        if df is not None and not getattr(df, "empty", True):
            return _as_int(df.iloc[0]["id_veiculo"])
    if id_guia is not None:
        df = dal.read(
            "SELECT id_veiculo FROM tb_guia WHERE id_guia = ? LIMIT 1",
            (id_guia,),
        )
        if df is not None and not getattr(df, "empty", True):
            return _as_int(df.iloc[0]["id_veiculo"])
    return None


def salvar_leitura_roleta(
    dal,
    body: dict[str, Any],
    id_usuario: int,
) -> dict[str, Any] | GuiaError:
    """
    Inicia ou finaliza leitura Ja E / RioCard.
    - Só ini → status iniciada
    - ini + fim → status finalizada + passageiros calculados
    - fim < ini → exige justificativa_virada (virada do contador)
    """
    sentido = str(body.get("sentido", "")).strip().lower()
    fonte = str(body.get("fonte", "")).strip().lower()
    if sentido not in SENTIDOS:
        return GuiaError("Sentido inválido (ida|volta).", "validacao")
    if fonte not in FONTES:
        return GuiaError("Fonte inválida (jae|riocard).", "validacao")

    id_viagem = _as_int(body.get("id_viagem"))
    id_guia = _as_int(body.get("id_guia"))
    id_trecho = _as_int(body.get("id_trecho"))
    if id_viagem is None and id_guia is None:
        return GuiaError("Informe id_viagem ou id_guia.", "validacao")

    id_veiculo = _resolver_veiculo(
        dal,
        id_veiculo=_as_int(body.get("id_veiculo")),
        id_viagem=id_viagem,
        id_guia=id_guia,
    )
    if id_veiculo is None:
        return GuiaError("Veículo não identificado para a leitura.", "validacao")

    # Vincula ao trecho: valida carro do trecho
    if id_trecho is not None:
        tr = dal.read(
            "SELECT id_guia, id_veiculo, status FROM tb_guia_trecho WHERE id_trecho = ?",
            (int(id_trecho),),
        )
        if tr is None or getattr(tr, "empty", True):
            return GuiaError("Trecho não encontrado para a leitura.", "nao_encontrado")
        if id_guia is None:
            id_guia = _as_int(tr.iloc[0].get("id_guia"))
        vei_t = _as_int(tr.iloc[0].get("id_veiculo"))
        if vei_t is not None and int(vei_t) != int(id_veiculo):
            return GuiaError(
                "Leitura deve ser do mesmo carro do trecho.",
                "carro_divergente",
            )
        st_t = str(tr.iloc[0].get("status") or "").strip().upper()
        if st_t == "CANCELADO":
            return GuiaError("Trecho cancelado.", "trecho_cancelado")

    leitura_ini = _as_int(body.get("leitura_ini"))
    leitura_fim = _as_int(body.get("leitura_fim"))
    if "leitura_ini" not in body and body.get("somente_fim"):
        # finalização: mantém ini existente
        pass
    elif leitura_ini is None and leitura_fim is None:
        return GuiaError("Informe ao menos a leitura inicial.", "validacao")

    justificativa = str(body.get("justificativa_virada", "") or "").strip()
    virada = 0
    if leitura_ini is not None and leitura_fim is not None and leitura_fim < leitura_ini:
        if not justificativa:
            return GuiaError(
                "Leitura final menor que a inicial: informe justificativa da virada do contador.",
                "virada_requer_justificativa",
            )
        virada = 1

    passageiros = calcular_passageiros(leitura_ini, leitura_fim, virada=bool(virada))
    status = "finalizada" if leitura_fim is not None and leitura_ini is not None else "iniciada"
    if leitura_ini is None and leitura_fim is not None:
        return GuiaError("Informe a leitura inicial antes da final.", "validacao")

    existente = _buscar_existente(
        dal, id_viagem=id_viagem, id_guia=id_guia, sentido=sentido, fonte=fonte
    )
    agora = _agora()

    # Troca de carro / mesmo carro: sugestão contextual
    if leitura_ini is None and existente is None:
        sug = sugerir_leitura_inicial(
            dal,
            id_veiculo=id_veiculo,
            fonte=fonte,
            sentido=sentido,
            id_guia=id_guia,
            id_trecho=id_trecho,
        )
        if sug is None and id_guia is not None:
            # Carro trocado ou sem histórico: exige leitura inicial explícita
            if body.get("usar_sugestao", True):
                return GuiaError(
                    "Informe a leitura inicial. "
                    "Troca de carro ou ausência de leitura anterior impede sugestão automática.",
                    "leituras_obrigatorias",
                )
        if sug is not None and body.get("usar_sugestao", True):
            leitura_ini = sug
            status = "iniciada" if leitura_fim is None else status
            passageiros = calcular_passageiros(
                leitura_ini, leitura_fim, virada=bool(virada)
            )

    if existente is None:
        if leitura_ini is None:
            return GuiaError("Informe a leitura inicial.", "validacao")
        ok = dal.create(
            """
            INSERT INTO tb_guia_roleta_leitura (
                id_viagem, id_guia, id_trecho, id_veiculo, sentido, fonte,
                leitura_ini, leitura_fim, passageiros, virada, justificativa_virada,
                status_leitura, id_usuario, criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_viagem,
                id_guia,
                id_trecho,
                id_veiculo,
                sentido,
                fonte,
                leitura_ini,
                leitura_fim,
                passageiros,
                virada,
                justificativa or None,
                status,
                id_usuario,
                agora,
                agora,
            ),
        )
        if not ok:
            return GuiaError("Falha ao salvar leitura.", "persistencia")
        df = dal.read(
            """
            SELECT id_leitura FROM tb_guia_roleta_leitura
            WHERE id_veiculo = ? AND sentido = ? AND fonte = ?
              AND COALESCE(id_viagem, -1) = COALESCE(?, -1)
              AND COALESCE(id_guia, -1) = COALESCE(?, -1)
            ORDER BY id_leitura DESC LIMIT 1
            """,
            (id_veiculo, sentido, fonte, id_viagem, id_guia),
        )
        id_leitura = int(df.iloc[0]["id_leitura"])
        _registrar_historico(
            dal,
            id_leitura=id_leitura,
            acao="iniciar" if leitura_fim is None else "finalizar",
            leitura_ini=leitura_ini,
            leitura_fim=leitura_fim,
            passageiros=passageiros,
            virada=virada,
            justificativa=justificativa or None,
            id_usuario=id_usuario,
        )
        row = _row_leitura(dal, id_leitura)
        assert row is not None
        row["sugestao_ini"] = sugerir_leitura_inicial(
            dal,
            id_veiculo=id_veiculo,
            fonte=fonte,
            sentido=sentido,
            excluir_id_leitura=id_leitura,
        )
        return row

    # Atualização — não perde ini se só enviar fim
    id_leitura = int(existente["id_leitura"])

    # Optimistic lock
    if "versao" in body or body.get("versao_esperada") is not None:
        try:
            esp = int(body.get("versao", body.get("versao_esperada")))
            atual_v = int(existente.get("versao") or 1)
        except (TypeError, ValueError):
            return GuiaError("Versão inválida.", "validacao")
        if esp != atual_v:
            return GuiaError(
                "Leitura alterada por outro usuário. Recarregue e tente novamente.",
                "conflito_versao",
            )

    ant_ini = _as_int(existente.get("leitura_ini"))
    ant_fim = _as_int(existente.get("leitura_fim"))
    if leitura_ini is None:
        leitura_ini = ant_ini
    if leitura_fim is None and "leitura_fim" not in body:
        leitura_fim = ant_fim

    # Edição de valor já salvo exige motivo
    edita_salvo = (
        (ant_ini is not None and "leitura_ini" in body and leitura_ini != ant_ini)
        or (ant_fim is not None and "leitura_fim" in body and leitura_fim != ant_fim)
    )
    motivo_edicao = str(body.get("motivo") or body.get("justificativa") or "").strip()
    if edita_salvo and len(motivo_edicao) < 5:
        return GuiaError(
            "Informe o motivo ao editar leitura já salva (mín. 5 caracteres).",
            "motivo_obrigatorio",
        )

    if leitura_ini is not None and leitura_fim is not None and leitura_fim < leitura_ini:
        if not justificativa:
            return GuiaError(
                "Leitura final menor que a inicial: informe justificativa da virada do contador.",
                "virada_requer_justificativa",
            )
        virada = 1
    elif leitura_fim is not None and leitura_ini is not None and leitura_fim >= leitura_ini:
        virada = 0
        justificativa = justificativa or None
    else:
        virada = int(existente.get("virada") or 0)
        justificativa = justificativa or existente.get("justificativa_virada")

    passageiros = calcular_passageiros(leitura_ini, leitura_fim, virada=bool(virada))
    status = (
        "finalizada"
        if leitura_ini is not None and leitura_fim is not None
        else "iniciada"
    )
    acao = "finalizar" if status == "finalizada" else "alterar"

    if edita_salvo and id_guia is not None:
        from .guia_jornada_service import _registrar_auditoria

        for campo, ant, novo in (
            ("leitura_ini", ant_ini, leitura_ini),
            ("leitura_fim", ant_fim, leitura_fim),
        ):
            if ant is not None and campo in body and ant != novo:
                err_a = _registrar_auditoria(
                    dal,
                    entidade="roleta",
                    id_entidade=id_leitura,
                    id_guia=id_guia,
                    id_usuario=int(id_usuario),
                    campo=f"{fonte}_{campo}",
                    valor_anterior=ant,
                    valor_novo=novo,
                    motivo=motivo_edicao,
                )
                if err_a:
                    return err_a

    ok = dal.update(
        """
        UPDATE tb_guia_roleta_leitura
        SET leitura_ini = ?, leitura_fim = ?, passageiros = ?,
            virada = ?, justificativa_virada = ?, status_leitura = ?,
            id_trecho = COALESCE(?, id_trecho),
            id_usuario = ?, atualizado_em = ?,
            versao = COALESCE(versao, 1) + 1
        WHERE id_leitura = ?
        """,
        (
            leitura_ini,
            leitura_fim,
            passageiros,
            virada,
            justificativa or None,
            status,
            id_trecho,
            id_usuario,
            agora,
            id_leitura,
        ),
    )
    if not ok:
        return GuiaError("Falha ao atualizar leitura.", "persistencia")
    _registrar_historico(
        dal,
        id_leitura=id_leitura,
        acao=acao,
        leitura_ini=leitura_ini,
        leitura_fim=leitura_fim,
        passageiros=passageiros,
        virada=virada,
        justificativa=justificativa or None,
        id_usuario=id_usuario,
    )
    row = _row_leitura(dal, id_leitura)
    assert row is not None
    row["sugestao_ini"] = sugerir_leitura_inicial(
        dal,
        id_veiculo=id_veiculo,
        fonte=fonte,
        sentido=sentido,
        excluir_id_leitura=id_leitura,
    )
    return row


def listar_leituras(
    dal,
    *,
    id_viagem: Optional[int] = None,
    id_guia: Optional[int] = None,
    id_veiculo: Optional[int] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if id_viagem is not None:
        clauses.append("r.id_viagem = ?")
        params.append(id_viagem)
    if id_guia is not None:
        clauses.append("r.id_guia = ?")
        params.append(id_guia)
    if id_veiculo is not None:
        clauses.append("r.id_veiculo = ?")
        params.append(id_veiculo)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    df = dal.read(
        f"""
        SELECT r.*, u.matricula AS matricula_usuario, u.nome AS nome_usuario
        FROM tb_guia_roleta_leitura r
        LEFT JOIN tb_usuario u ON u.id_usuario = r.id_usuario
        {where}
        ORDER BY r.atualizado_em ASC, r.id_leitura ASC
        """,
        tuple(params) if params else None,
    )
    if df is None or getattr(df, "empty", True):
        return []
    return [_safe_row(r) for r in df.to_dict(orient="records")]


def historico_leitura(dal, id_leitura: int) -> list[dict[str, Any]] | GuiaError:
    if _row_leitura(dal, id_leitura) is None:
        return GuiaError("Leitura não encontrada.", "nao_encontrado")
    df = dal.read(
        """
        SELECT h.*, u.matricula AS matricula_usuario, u.nome AS nome_usuario
        FROM tb_guia_roleta_historico h
        LEFT JOIN tb_usuario u ON u.id_usuario = h.id_usuario
        WHERE h.id_leitura = ?
        ORDER BY h.registrado_em ASC, h.id_historico ASC
        """,
        (id_leitura,),
    )
    if df is None or getattr(df, "empty", True):
        return []
    return [_safe_row(r) for r in df.to_dict(orient="records")]


def bloco_fonte(leitura: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not leitura:
        return {
            "leitura_ini": None,
            "leitura_fim": None,
            "passageiros": None,
            "status_leitura": None,
            "virada": False,
            "justificativa_virada": None,
            "id_leitura": None,
            "id_usuario": None,
            "atualizado_em": None,
        }
    return {
        "leitura_ini": _as_int(leitura.get("leitura_ini")),
        "leitura_fim": _as_int(leitura.get("leitura_fim")),
        "passageiros": _as_int(leitura.get("passageiros")),
        "status_leitura": leitura.get("status_leitura"),
        "virada": bool(int(leitura.get("virada") or 0)),
        "justificativa_virada": leitura.get("justificativa_virada"),
        "id_leitura": _as_int(leitura.get("id_leitura")),
        "id_usuario": _as_int(leitura.get("id_usuario")),
        "nome_usuario": leitura.get("nome_usuario"),
        "atualizado_em": leitura.get("atualizado_em"),
    }
