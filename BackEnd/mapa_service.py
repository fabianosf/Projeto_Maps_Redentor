# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Regras de negócio do módulo MAPA — RF-MAP-RN-001..008."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

from .cadastros_service import CadastroError, criar_veiculo
from .constants import COD_MAP_INSERT_RETRIES, COD_MAP_MAX

STATUS_ESCALA_EM_ANDAMENTO = "EM_ANDAMENTO"
STATUS_ESCALA_ENCERRADA = "ENCERRADA"


@dataclass(frozen=True)
class MapaError:
    mensagem: str
    codigo: str = "mapa_erro"


def _parse_date(value: Any) -> date | MapaError:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    texto = str(value or "").strip()
    if not texto:
        return MapaError("Data é obrigatória.", "validacao")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return MapaError("Data inválida.", "validacao")


def _parse_datetime(value: Any) -> datetime | MapaError:
    if isinstance(value, datetime):
        return value
    texto = str(value or "").strip()
    if not texto:
        return MapaError("Data/hora é obrigatória.", "validacao")
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
    ):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    return MapaError("Data/hora inválida.", "validacao")


def _parse_datetime_optional(value: Any) -> datetime | None | MapaError:
    """FIM DE JORNADA — aceita vazio/null."""
    if value is None:
        return None
    texto = str(value).strip()
    if not texto or texto.lower() in ("null", "none"):
        return None
    return _parse_datetime(texto)


def _garantir_locais_padrao(dal) -> tuple[int, int] | MapaError:
    """Garante 2 locais para FK de tb_linha."""
    existentes = dal.read(
        "SELECT id_local, codigo_local FROM tb_local WHERE ativo = 1 ORDER BY codigo_local"
    )
    ids: list[int] = []
    if not existentes.empty:
        ids = [int(r["id_local"]) for _, r in existentes.iterrows()]
    while len(ids) < 2:
        codigo = 10 + len(ids) * 10
        ok = dal.create(
            "INSERT INTO tb_local (codigo_local, descricao, ativo) VALUES (?, ?, 1)",
            (codigo, f"Local {codigo}"),
        )
        if not ok:
            return MapaError("Falha ao preparar locais da linha.", "persistencia")
        row = dal.read(
            "SELECT id_local FROM tb_local WHERE codigo_local = ?",
            (codigo,),
        )
        if row.empty:
            return MapaError("Falha ao preparar locais da linha.", "persistencia")
        ids.append(int(row.iloc[0]["id_local"]))
    return ids[0], ids[1]


def _id_pk_informado(valor: Any) -> bool:
    """True se o cliente enviou PK (inclui 0 — seeds usam id a partir de zero)."""
    return valor is not None and valor != ""


def _resolver_id_empresa(dal, payload: dict[str, Any]) -> int | None:
    """Resolve id_empresa por PK, codigo_empresa ou descricao (campo empresa)."""
    id_empresa = payload.get("id_empresa")
    if _id_pk_informado(id_empresa):
        empresa = dal.read(
            "SELECT id_empresa FROM tb_empresa WHERE id_empresa = ? AND ativo = 1",
            (int(id_empresa),),
        )
        if empresa.empty and int(id_empresa) != 0:
            empresa = dal.read(
                "SELECT id_empresa FROM tb_empresa WHERE codigo_empresa = ? AND ativo = 1",
                (int(id_empresa),),
            )
        if not empresa.empty:
            return int(empresa.iloc[0]["id_empresa"])

    descricao = str(payload.get("empresa") or "").strip()
    if descricao:
        empresa = dal.read(
            """
            SELECT id_empresa FROM tb_empresa
            WHERE LOWER(TRIM(descricao)) = LOWER(?) AND ativo = 1
            """,
            (descricao,),
        )
        if not empresa.empty:
            return int(empresa.iloc[0]["id_empresa"])

        # Cria sob demanda (combo UI: Futuro/Redentor/Barra) alinhado ao seed.
        codigos_conhecidos = {"redentor": 1, "futuro": 2, "barra": 3}
        codigo = codigos_conhecidos.get(descricao.lower())
        if codigo is None:
            max_df = dal.read(
                "SELECT COALESCE(MAX(codigo_empresa), 0) AS max_cod FROM tb_empresa"
            )
            codigo = int(max_df.iloc[0]["max_cod"]) + 1
        ok = dal.create(
            """
            INSERT INTO tb_empresa (codigo_empresa, descricao, ativo)
            VALUES (?, ?, 1)
            """,
            (codigo, descricao),
        )
        if not ok:
            return None
        criada = dal.read(
            """
            SELECT id_empresa FROM tb_empresa
            WHERE LOWER(TRIM(descricao)) = LOWER(?) AND ativo = 1
            """,
            (descricao,),
        )
        if not criada.empty:
            return int(criada.iloc[0]["id_empresa"])

    return None


def _resolver_id_turno(dal, payload: dict[str, Any]) -> int | MapaError:
    id_turno = payload.get("id_turno")
    if _id_pk_informado(id_turno):
        turno = dal.read(
            "SELECT id_turno FROM tb_turno WHERE id_turno = ? AND ativo = 1",
            (int(id_turno),),
        )
        if not turno.empty:
            return int(turno.iloc[0]["id_turno"])
        # tenta por codigo_turno igual ao valor enviado (exceto 0, que é PK válida)
        if int(id_turno) != 0:
            turno = dal.read(
                "SELECT id_turno FROM tb_turno WHERE codigo_turno = ? AND ativo = 1",
                (int(id_turno),),
            )
            if not turno.empty:
                return int(turno.iloc[0]["id_turno"])

    codigo = payload.get("codigo_turno")
    if codigo not in (None, ""):
        turno = dal.read(
            "SELECT id_turno FROM tb_turno WHERE codigo_turno = ? AND ativo = 1",
            (int(codigo),),
        )
        if not turno.empty:
            return int(turno.iloc[0]["id_turno"])

    descricao = str(payload.get("turno") or "").strip().upper()
    if descricao:
        turno = dal.read(
            "SELECT id_turno FROM tb_turno WHERE UPPER(TRIM(descricao)) = ? AND ativo = 1",
            (descricao,),
        )
        if not turno.empty:
            return int(turno.iloc[0]["id_turno"])

    return MapaError("Turno inválido ou inativo.", "validacao")


def _resolver_id_linha(dal, payload: dict[str, Any]) -> int | MapaError:
    """Resolve id_linha por PK, codigo_linha ou cria a linha sob demanda."""
    id_linha = payload.get("id_linha")
    if _id_pk_informado(id_linha):
        linha = dal.read(
            "SELECT id_linha FROM tb_linha WHERE id_linha = ? AND ativo = 1",
            (int(id_linha),),
        )
        if not linha.empty:
            return int(linha.iloc[0]["id_linha"])

    codigo_raw = payload.get("codigo_linha")
    if codigo_raw in (None, ""):
        return MapaError("Linha é obrigatória.", "validacao")
    try:
        codigo_int = int(str(codigo_raw).strip())
    except (TypeError, ValueError):
        return MapaError("Linha inválida.", "validacao")
    if codigo_int <= 0:
        return MapaError("Linha inválida.", "validacao")

    id_empresa_ok = _resolver_id_empresa(dal, payload)
    if id_empresa_ok is None:
        return MapaError("Empresa é obrigatória para cadastrar a linha.", "validacao")

    existente = dal.read(
        """
        SELECT id_linha FROM tb_linha
        WHERE codigo_linha = ? AND id_empresa = ? AND ativo = 1
        """,
        (codigo_int, id_empresa_ok),
    )
    if not existente.empty:
        return int(existente.iloc[0]["id_linha"])

    locais = _garantir_locais_padrao(dal)
    if isinstance(locais, MapaError):
        return locais
    id_origem, id_destino = locais

    descricao = str(codigo_int).zfill(3)
    ok = dal.create(
        """
        INSERT INTO tb_linha (
            codigo_linha, id_empresa, descricao,
            id_local_origem, id_local_destino, ativo
        ) VALUES (?, ?, ?, ?, ?, 1)
        """,
        (codigo_int, id_empresa_ok, descricao, id_origem, id_destino),
    )
    if not ok:
        # Corrida / UNIQUE (id_empresa, codigo_linha)
        existente = dal.read(
            """
            SELECT id_linha FROM tb_linha
            WHERE codigo_linha = ? AND id_empresa = ?
            """,
            (codigo_int, id_empresa_ok),
        )
        if not existente.empty:
            return int(existente.iloc[0]["id_linha"])
        return MapaError("Falha ao cadastrar a linha.", "persistencia")

    criada = dal.read(
        """
        SELECT id_linha FROM tb_linha
        WHERE codigo_linha = ? AND id_empresa = ?
        """,
        (codigo_int, id_empresa_ok),
    )
    if criada.empty:
        return MapaError("Falha ao cadastrar a linha.", "persistencia")
    return int(criada.iloc[0]["id_linha"])


def _gerar_proximo_cod_map(dal) -> int | MapaError:
    df = dal.read("SELECT COALESCE(MAX(cod_map), 0) AS max_cod FROM tb_map")
    proximo = int(df.iloc[0]["max_cod"]) + 1
    if proximo > COD_MAP_MAX:
        return MapaError("Limite de cod_map esgotado.", "cod_map_esgotado")
    return proximo


def listar_mapas(dal) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT m.id_registro, m.cod_map, m.data,
               COALESCE(e_hdr.descricao, e_item.descricao) AS empresa,
               CAST(COALESCE(l_hdr.codigo_linha, l_item.codigo_linha) AS CHAR) AS linha,
               t.descricao AS turno,
               u.nome AS despachante
        FROM tb_map m
        INNER JOIN tb_turno t ON t.id_turno = m.id_turno
        INNER JOIN tb_usuario u ON u.id_usuario = m.id_usuario
        LEFT JOIN tb_linha l_hdr ON l_hdr.id_linha = m.id_linha
        LEFT JOIN tb_empresa e_hdr ON e_hdr.id_empresa = l_hdr.id_empresa
        LEFT JOIN tb_item_map i0 ON i0.id_item = (
            SELECT MIN(i2.id_item) FROM tb_item_map i2 WHERE i2.idmap = m.id_registro
        )
        LEFT JOIN tb_linha l_item ON l_item.id_linha = i0.id_linha
        LEFT JOIN tb_empresa e_item ON e_item.id_empresa = l_item.id_empresa
        ORDER BY m.data DESC, m.cod_map DESC
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def obter_indicadores(
    dal, id_linha: int | None = None
) -> dict[str, Any] | MapaError:
    """
    Qtc/M — média de passageiros (ida+volta) da linha no dia atual (tb_map.data).
    Requer id_linha de tb_linha.
    """
    if id_linha is None:
        return {
            "qtc_m": None,
            "id_linha": None,
            "codigo_linha": None,
        }

    try:
        id_linha_int = int(id_linha)
    except (TypeError, ValueError):
        return MapaError("Linha inválida.", "validacao")

    linha_df = dal.read(
        """
        SELECT id_linha, codigo_linha
        FROM tb_linha
        WHERE id_linha = ? AND ativo = 1
        """,
        (id_linha_int,),
    )
    if linha_df.empty:
        return MapaError("Linha não encontrada.", "nao_encontrado")

    codigo_linha = linha_df.iloc[0]["codigo_linha"]
    try:
        codigo_exibicao = int(codigo_linha)
    except (TypeError, ValueError):
        codigo_exibicao = codigo_linha

    df = dal.read(
        """
        SELECT AVG(
                   COALESCE(v.qtd_pas_ida, 0) + COALESCE(v.qtd_pas_volta, 0)
               ) AS qtc_m
        FROM tb_map m
        INNER JOIN tb_item_map i ON i.idmap = m.id_registro
        INNER JOIN tb_viagem v ON v.id_item_registro = i.id_item
        WHERE i.id_linha = ?
          AND m.data = CURDATE()
        """,
        (id_linha_int,),
    )
    qtc_m: float | None = None
    if not df.empty and df.iloc[0]["qtc_m"] is not None:
        try:
            qtc_m = round(float(df.iloc[0]["qtc_m"]), 1)
        except (TypeError, ValueError):
            qtc_m = None

    return {
        "qtc_m": qtc_m,
        "id_linha": id_linha_int,
        "codigo_linha": codigo_exibicao,
    }


def obter_mapa_completo(dal, id_registro: int) -> dict[str, Any] | MapaError:
    cab = dal.read(
        """
        SELECT m.*,
               l_hdr.id_empresa AS id_empresa,
               l_hdr.descricao AS linha,
               e_hdr.descricao AS empresa,
               t.descricao AS turno,
               u.nome AS despachante,
               u.matricula AS matricula_despachante
        FROM tb_map m
        INNER JOIN tb_turno t ON t.id_turno = m.id_turno
        INNER JOIN tb_usuario u ON u.id_usuario = m.id_usuario
        LEFT JOIN tb_linha l_hdr ON l_hdr.id_linha = m.id_linha
        LEFT JOIN tb_empresa e_hdr ON e_hdr.id_empresa = l_hdr.id_empresa
        WHERE m.id_registro = ?
        """,
        (id_registro,),
    )
    if cab.empty:
        return MapaError("MAPA não encontrado.", "nao_encontrado")

    itens_df = dal.read(
        """
        SELECT i.*,
               v.numero_frota, v.placa, v.id_empresa AS id_empresa_veiculo,
               l.id_linha AS id_linha,
               l.codigo_linha,
               l.descricao AS linha,
               e.id_empresa AS id_empresa,
               e.descricao AS empresa,
               mot.nome AS motorista, mot.matricula AS matricula_motorista
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_linha l ON l.id_linha = i.id_linha
        INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE i.idmap = ?
        ORDER BY i.id_item
        """,
        (id_registro,),
    )

    itens: list[dict[str, Any]] = []
    for _, item_row in itens_df.iterrows():
        item = item_row.to_dict()
        id_item = int(item["id_item"])
        item["id_mapa_item"] = id_item
        st = str(item.get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO).strip().upper()
        item["status_escala"] = st or STATUS_ESCALA_EM_ANDAMENTO
        _enriquecer_campos_horas_item(item)
        viagens_df = dal.read(
            """
            SELECT * FROM tb_viagem
            WHERE id_item_registro = ?
            ORDER BY id_viagem
            """,
            (id_item,),
        )
        viagens = (
            viagens_df.to_dict(orient="records") if not viagens_df.empty else []
        )
        for v in viagens:
            v["id_mapa_item"] = int(v.get("id_item_registro") or id_item)
        item["viagens"] = viagens
        itens.append(item)

    resultado = cab.iloc[0].to_dict()
    data_ok = _coerce_mapa_date(resultado.get("data"))
    if data_ok is not None:
        resultado["data"] = data_ok.strftime("%Y-%m-%d")
    resultado["itens"] = itens
    return resultado


def _resolver_ou_criar_veiculo_mapa(
    dal, payload: dict[str, Any], id_empresa: int
) -> int | MapaError:
    """Valida frota do cabeçalho; cria veículo se não existir; exige mesma empresa."""
    frota_raw = payload.get("numero_frota")
    if frota_raw is None or str(frota_raw).strip() == "":
        frota_raw = payload.get("veiculo")
    frota = str(frota_raw or "").strip().upper()
    if not frota:
        return MapaError("Veículo é obrigatório.", "validacao")

    existente = dal.read(
        """
        SELECT id_veiculo, id_empresa, numero_frota, ativo
        FROM tb_veiculo
        WHERE UPPER(TRIM(numero_frota)) = ?
        LIMIT 1
        """,
        (frota,),
    )
    if not existente.empty:
        row = existente.iloc[0]
        if int(row.get("ativo") or 0) not in (1, True):
            return MapaError(f"Veículo {frota} está inativo.", "validacao")
        id_emp_vei = row["id_empresa"]
        if id_emp_vei is None or int(id_emp_vei) != int(id_empresa):
            return MapaError(
                f"Veículo {frota} não pertence à empresa selecionada.",
                "validacao",
            )
        return int(row["id_veiculo"])

    criado = criar_veiculo(dal, numero_frota=frota, id_empresa=int(id_empresa))
    if isinstance(criado, CadastroError):
        return MapaError(criado.mensagem, criado.codigo)
    return int(criado["id_veiculo"])


def criar_mapa(dal, id_usuario: int, payload: dict[str, Any]) -> dict[str, Any] | MapaError:
    """Cria cabeçalho do MAPA (turno/data/plantão). Sem empresa/linha/veículo/item."""
    id_turno = _resolver_id_turno(dal, payload)
    if isinstance(id_turno, MapaError):
        return id_turno

    data_parsed = _parse_date(payload.get("data"))
    if isinstance(data_parsed, MapaError):
        return data_parsed

    inicio = _parse_datetime(payload.get("inicio_jornada_des"))
    fim = _parse_datetime_optional(payload.get("fim_jornada_des"))
    if isinstance(inicio, MapaError):
        return inicio
    if isinstance(fim, MapaError):
        return fim
    if fim is not None and inicio >= fim:
        return MapaError("Início da jornada deve ser anterior ao fim.", "validacao")

    observacao = payload.get("observacao")
    fim_sql = fim.strftime("%Y-%m-%d %H:%M:%S") if fim is not None else None

    last_error: MapaError | None = None
    for _ in range(COD_MAP_INSERT_RETRIES):
        cod_map = _gerar_proximo_cod_map(dal)
        if isinstance(cod_map, MapaError):
            return cod_map

        try:
            ok_map = dal.create(
                """
                INSERT INTO tb_map (
                    cod_map, id_usuario, id_linha, id_turno, data,
                    inicio_jornada_des, fim_jornada_des, observacao
                ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                """,
                (
                    cod_map,
                    id_usuario,
                    int(id_turno),
                    data_parsed.isoformat(),
                    inicio.strftime("%Y-%m-%d %H:%M:%S"),
                    fim_sql,
                    observacao,
                ),
            )
            if not ok_map:
                last_error = MapaError(
                    "Conflito ao gerar cod_map. Tente novamente.",
                    "cod_map_conflito",
                )
                continue

            row = dal.read(
                "SELECT id_registro FROM tb_map WHERE cod_map = ?",
                (cod_map,),
            )
            if row.empty:
                return MapaError("Falha ao criar MAPA.", "persistencia")
            id_registro = int(row.iloc[0]["id_registro"])
            completo = obter_mapa_completo(dal, id_registro)
            assert not isinstance(completo, MapaError)
            return completo
        except Exception:
            last_error = MapaError(
                "Conflito ao gerar cod_map. Tente novamente.",
                "cod_map_conflito",
            )
            continue

    return last_error or MapaError("Falha ao criar MAPA.", "persistencia")


def atualizar_mapa(
    dal, id_registro: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    existe = dal.read(
        "SELECT id_registro FROM tb_map WHERE id_registro = ?",
        (id_registro,),
    )
    if existe.empty:
        return MapaError("MAPA não encontrado.", "nao_encontrado")

    id_turno = _resolver_id_turno(dal, payload)
    if isinstance(id_turno, MapaError):
        return id_turno

    data_parsed = _parse_date(payload.get("data"))
    if isinstance(data_parsed, MapaError):
        return data_parsed

    inicio = _parse_datetime(payload.get("inicio_jornada_des"))
    fim = _parse_datetime_optional(payload.get("fim_jornada_des"))
    if isinstance(inicio, MapaError):
        return inicio
    if isinstance(fim, MapaError):
        return fim
    if fim is not None and inicio >= fim:
        return MapaError("Início da jornada deve ser anterior ao fim.", "validacao")

    observacao = payload.get("observacao")
    fim_sql = fim.strftime("%Y-%m-%d %H:%M:%S") if fim is not None else None

    ok = dal.update(
        """
        UPDATE tb_map
        SET id_turno = ?, data = ?,
            inicio_jornada_des = ?, fim_jornada_des = ?, observacao = ?
        WHERE id_registro = ?
        """,
        (
            int(id_turno),
            data_parsed.isoformat(),
            inicio.strftime("%Y-%m-%d %H:%M:%S"),
            fim_sql,
            observacao,
            id_registro,
        ),
    )
    if not ok:
        return MapaError("Falha ao atualizar MAPA.", "persistencia")

    completo = obter_mapa_completo(dal, id_registro)
    if isinstance(completo, MapaError):
        return completo
    return completo


def excluir_mapa(dal, id_registro: int) -> MapaError | None:
    itens = dal.read(
        "SELECT id_item FROM tb_item_map WHERE idmap = ?",
        (id_registro,),
    )
    for _, row in itens.iterrows():
        id_item = int(row["id_item"])
        dal.delete(
            "DELETE FROM tb_viagem WHERE id_item_registro = ?",
            (id_item,),
        )
    dal.delete("DELETE FROM tb_item_map WHERE idmap = ?", (id_registro,))
    ok = dal.delete("DELETE FROM tb_map WHERE id_registro = ?", (id_registro,))
    if not ok:
        return MapaError("MAPA não encontrado.", "nao_encontrado")
    return None


def _resolver_id_veiculo(dal, payload: dict[str, Any]) -> int | MapaError:
    """Resolve veículo pela coluna numero_frota (prioritária) ou id_veiculo."""
    frota_raw = payload.get("numero_frota")
    if frota_raw is None or str(frota_raw).strip() == "":
        frota_raw = payload.get("carro")
    frota = str(frota_raw or "").strip()
    if frota:
        digits = "".join(ch for ch in frota if ch.isdigit())
        # Busca exclusivamente em tb_veiculo.numero_frota
        df = dal.read(
            """
            SELECT id_veiculo
            FROM tb_veiculo
            WHERE ativo = 1
              AND (
                    numero_frota = ?
                 OR TRIM(LEADING '0' FROM numero_frota) = TRIM(LEADING '0' FROM ?)
                 OR (CAST(numero_frota AS UNSIGNED) = CAST(? AS UNSIGNED) AND ? REGEXP '^[0-9]+$')
              )
            LIMIT 1
            """,
            (frota, digits or frota, digits or frota, digits or frota),
        )
        if df.empty:
            return MapaError("Carro não encontrado.", "validacao")
        return int(df.iloc[0]["id_veiculo"])

    id_veiculo = payload.get("id_veiculo")
    if id_veiculo is not None and str(id_veiculo).strip() != "":
        df = dal.read(
            """
            SELECT id_veiculo FROM tb_veiculo
            WHERE ativo = 1 AND id_veiculo = ?
            LIMIT 1
            """,
            (int(id_veiculo),),
        )
        if df.empty:
            return MapaError("Carro não encontrado.", "validacao")
        return int(df.iloc[0]["id_veiculo"])

    return MapaError("Carro é obrigatório.", "validacao")


def _resolver_id_motorista(dal, payload: dict[str, Any]) -> int | MapaError:
    """Resolve motorista exclusivamente pela coluna tb_motorista.matricula (ou id)."""
    mat_raw = payload.get("matricula")
    if mat_raw is None or str(mat_raw).strip() == "":
        mat_raw = payload.get("matricula_motorista")
    matricula = str(mat_raw or "").strip()
    if matricula:
        digits = "".join(ch for ch in matricula if ch.isdigit())
        # Busca apenas na coluna matricula (nunca em id_motorista / nome).
        df = dal.read(
            """
            SELECT id_motorista
            FROM tb_motorista
            WHERE ativo = 1
              AND (
                    matricula = ?
                 OR TRIM(LEADING '0' FROM matricula) = TRIM(LEADING '0' FROM ?)
                 OR (CAST(matricula AS UNSIGNED) = CAST(? AS UNSIGNED) AND ? REGEXP '^[0-9]+$')
              )
            LIMIT 1
            """,
            (matricula, digits or matricula, digits or matricula, digits or matricula),
        )
        if df.empty:
            return MapaError("Matrícula não encontrada.", "validacao")
        return int(df.iloc[0]["id_motorista"])

    id_motorista = payload.get("id_motorista")
    if id_motorista is not None and str(id_motorista).strip() != "":
        df = dal.read(
            """
            SELECT id_motorista FROM tb_motorista
            WHERE ativo = 1 AND id_motorista = ?
            LIMIT 1
            """,
            (int(id_motorista),),
        )
        if df.empty:
            return MapaError("Matrícula não encontrada.", "validacao")
        return int(df.iloc[0]["id_motorista"])

    return MapaError("Matrícula é obrigatória.", "validacao")


def _erro_veiculo_ja_alocado(
    dal,
    idmap: int,
    id_veiculo: int,
    id_item_excluir: int | None = None,
) -> MapaError | None:
    """
    Veículo em escala EM_ANDAMENTO (qualquer MAPA) bloqueia nova vinculação.
    idmap mantido na assinatura por compatibilidade com chamadas existentes.
    """
    del idmap  # ocupação é global por status
    params: list[Any] = [int(id_veiculo), STATUS_ESCALA_EM_ANDAMENTO]
    sql = """
        SELECT i.id_item, v.numero_frota, m.cod_map
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_veiculo = ?
          AND UPPER(TRIM(i.status_escala)) = ?
    """
    if id_item_excluir is not None:
        sql += " AND i.id_item <> ?"
        params.append(int(id_item_excluir))
    sql += " LIMIT 1"
    existe = dal.read(sql, tuple(params))
    if existe.empty:
        return None
    frota = str(existe.iloc[0].get("numero_frota") or id_veiculo).strip().upper()
    try:
        cod_map = int(existe.iloc[0].get("cod_map") or 0)
    except (TypeError, ValueError):
        cod_map = 0
    num_map = f"{cod_map:05d}" if cod_map else str(existe.iloc[0].get("cod_map") or "—")
    return MapaError(
        f"O veículo {frota} está em operação no MAPA {num_map}. "
        "Dê baixa antes de vinculá-lo novamente.",
        "conflito_veiculo",
    )


def _erro_motorista_ja_alocado(
    dal,
    idmap: int,
    id_motorista: int,
    id_item_excluir: int | None = None,
) -> MapaError | None:
    """Motorista em escala EM_ANDAMENTO (qualquer MAPA) bloqueia nova vinculação."""
    del idmap
    params: list[Any] = [int(id_motorista), STATUS_ESCALA_EM_ANDAMENTO]
    sql = """
        SELECT i.id_item, mot.matricula, mot.nome, v.numero_frota
        FROM tb_item_map i
        INNER JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        WHERE i.id_motorista = ?
          AND UPPER(TRIM(i.status_escala)) = ?
    """
    if id_item_excluir is not None:
        sql += " AND i.id_item <> ?"
        params.append(int(id_item_excluir))
    sql += " LIMIT 1"
    existe = dal.read(sql, tuple(params))
    if existe.empty:
        return None
    mat = str(existe.iloc[0].get("matricula") or "").strip()
    nome = str(existe.iloc[0].get("nome") or "").strip()
    rotulo = " — ".join(p for p in (mat, nome) if p) or str(id_motorista)
    frota = str(existe.iloc[0].get("numero_frota") or "").strip().upper() or "—"
    return MapaError(
        f"O motorista {rotulo} está em operação no veículo {frota}. "
        "Dê baixa antes de vinculá-lo novamente.",
        "conflito_motorista",
    )


def listar_ocupacao_escalas(
    dal, filtros: dict[str, Any] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """
    Veículos e motoristas em escalas EM_ANDAMENTO.
    Filtros opcionais: id_mapa, id_empresa, id_linha, data.
    """
    filtros = dict(filtros or {})
    where = ["UPPER(TRIM(i.status_escala)) = ?"]
    params: list[Any] = [STATUS_ESCALA_EM_ANDAMENTO]

    id_mapa = filtros.get("id_mapa")
    if id_mapa not in (None, ""):
        where.append("i.idmap = ?")
        params.append(int(id_mapa))

    id_empresa = filtros.get("id_empresa")
    if id_empresa not in (None, ""):
        where.append("l.id_empresa = ?")
        params.append(int(id_empresa))

    id_linha = filtros.get("id_linha")
    if id_linha not in (None, ""):
        where.append("i.id_linha = ?")
        params.append(int(id_linha))

    data_ref = filtros.get("data")
    if data_ref not in (None, ""):
        data_ok = _parse_date(data_ref)
        if not isinstance(data_ok, MapaError):
            where.append("m.data = ?")
            params.append(data_ok.strftime("%Y-%m-%d"))

    where_sql = " AND ".join(where)
    df = dal.read(
        f"""
        SELECT i.id_item, i.idmap, i.id_veiculo, i.id_motorista, i.status_escala,
               i.inicio_real, i.chegada_ponto, i.hor_ini_jor,
               v.numero_frota,
               mot.matricula AS matricula_motorista, mot.nome AS nome_motorista,
               m.cod_map, m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        INNER JOIN tb_linha l ON l.id_linha = i.id_linha
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE {where_sql}
        ORDER BY v.numero_frota, i.id_item
        """,
        tuple(params),
    )

    veiculos_ocupados: list[dict[str, Any]] = []
    motoristas_ocupados: list[dict[str, Any]] = []
    if df.empty:
        return {
            "veiculos_ocupados": veiculos_ocupados,
            "motoristas_ocupados": motoristas_ocupados,
            # aliases legados (compatibilidade)
            "veiculos": veiculos_ocupados,
            "motoristas": motoristas_ocupados,
        }

    for _, row in df.iterrows():
        inicio_dt = (
            _as_datetime(row.get("inicio_real"))
            or _as_datetime(row.get("chegada_ponto"))
            or _as_datetime(row.get("hor_ini_jor"))
        )
        inicio_hhmm = _format_hhmm(inicio_dt) if inicio_dt else None
        prefixo = str(row.get("numero_frota") or "").strip().upper()
        status = (
            str(row.get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO)
            .strip()
            .upper()
            or STATUS_ESCALA_EM_ANDAMENTO
        )
        id_item = int(row["id_item"])
        id_mapa_val = int(row["idmap"])
        id_veiculo = int(row["id_veiculo"])
        id_mot_raw = row.get("id_motorista")
        id_motorista = None
        try:
            if id_mot_raw is not None and str(id_mot_raw).strip() not in (
                "",
                "None",
                "nan",
            ):
                id_motorista = int(id_mot_raw)
        except (TypeError, ValueError):
            id_motorista = None

        mat = str(row.get("matricula_motorista") or "").strip() or None
        nome = str(row.get("nome_motorista") or "").strip() or None

        veiculos_ocupados.append(
            {
                "id_veiculo": id_veiculo,
                "prefixo": prefixo,
                "numero_frota": prefixo,
                "id_mapa_item": id_item,
                "id_item": id_item,
                "id_mapa": id_mapa_val,
                "idmap": id_mapa_val,
                "cod_map": int(row["cod_map"]) if row.get("cod_map") is not None else None,
                "id_motorista": id_motorista,
                "matricula_motorista": mat,
                "nome_motorista": nome,
                "inicio_real": inicio_hhmm,
                "status": status,
                "status_escala": status,
            }
        )
        if id_motorista is not None:
            motoristas_ocupados.append(
                {
                    "id_motorista": id_motorista,
                    "matricula": mat,
                    "nome": nome,
                    "id_mapa_item": id_item,
                    "id_item": id_item,
                    "id_mapa": id_mapa_val,
                    "idmap": id_mapa_val,
                    "cod_map": int(row["cod_map"]) if row.get("cod_map") is not None else None,
                    "id_veiculo": id_veiculo,
                    "prefixo_veiculo": prefixo,
                    "numero_frota": prefixo,
                    "inicio_real": inicio_hhmm,
                    "status": status,
                    "status_escala": status,
                }
            )

    return {
        "veiculos_ocupados": veiculos_ocupados,
        "motoristas_ocupados": motoristas_ocupados,
        "veiculos": veiculos_ocupados,
        "motoristas": motoristas_ocupados,
    }


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if getattr(value, "tzinfo", None) else value
    # pandas.Timestamp / tipos com to_pydatetime
    to_py = getattr(value, "to_pydatetime", None)
    if callable(to_py):
        try:
            dt = to_py()
            if isinstance(dt, datetime):
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except Exception:
            pass
    texto = str(value).strip()
    if not texto or texto.lower() in ("none", "null", "nat", "nan"):
        return None
    texto = texto.replace("T", " ")
    texto = re.sub(r"\s*(GMT|UTC|Z)$", "", texto, flags=re.IGNORECASE).strip()
    texto = re.sub(r"([+-]\d{2}:?\d{2})$", "", texto).strip()
    candidatos = [texto]
    if len(texto) >= 19:
        candidatos.insert(0, texto[:19])
    elif len(texto) == 16:
        candidatos.insert(0, texto + ":00")
    for candidato in candidatos:
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%H:%M:%S",
            "%H:%M",
        ):
            try:
                dt = datetime.strptime(candidato, fmt)
                if fmt in ("%H:%M:%S", "%H:%M"):
                    # Sem data: sentinela para combinar com data do MAPA depois
                    return datetime(1900, 1, 1, dt.hour, dt.minute, dt.second)
                return dt
            except ValueError:
                continue
    return None


def _combinar_com_data_mapa(dt: datetime | None, data_mapa: Any) -> datetime | None:
    """Se dt veio só com hora (data 1900-01-01), aplica a data do MAPA."""
    if dt is None:
        return None
    if dt.year != 1900 or dt.month != 1 or dt.day != 1:
        return dt
    base = _coerce_mapa_date(data_mapa)
    if base is None:
        return None
    return datetime(base.year, base.month, base.day, dt.hour, dt.minute, dt.second)


def _format_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _duracao_minutos(inicio: datetime, fim: datetime) -> int:
    """Minutos trabalhados (fim - inicio); suporta cruzamento de meia-noite."""
    delta = fim - inicio
    return int(delta.total_seconds() // 60)


def _format_hhmm_from_minutos(minutos: int) -> str:
    m = max(0, int(minutos))
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}"


def _intervalos_sobrepoem(
    a0: datetime, a1: datetime | None, b0: datetime, b1: datetime | None
) -> bool:
    """
    Sobreposição com extremos abertos à direita: [a0, a1) e [b0, b1).
    a1/b1 None = intervalo aberto (em andamento).
    Limite igual (a1 == b0) NÃO sobrepõe — permite troca no mesmo instante.
    """
    fim_a = a1 if a1 is not None else datetime.max
    fim_b = b1 if b1 is not None else datetime.max
    return a0 < fim_b and b0 < fim_a


def _resolver_inicio_real_item(
    payload: dict[str, Any],
    chegada: datetime | None,
    hor_ini: datetime | None,
) -> datetime:
    raw = payload.get("inicio_real", payload.get("inicio_real_jornada"))
    parsed = _as_datetime(raw) if raw is not None else None
    if parsed is not None:
        return parsed
    if chegada is not None:
        return chegada
    if hor_ini is not None:
        return hor_ini
    return datetime.now().replace(second=0, microsecond=0)


def _erro_sobreposicao_motorista(
    dal,
    id_motorista: int,
    inicio: datetime,
    fim: datetime | None,
    id_item_excluir: int | None = None,
) -> MapaError | None:
    """Bloqueia sobreposição de intervalos reais (ou planejados se real ausente)."""
    rows = dal.read(
        """
        SELECT id_item, inicio_real, fim_real, hor_ini_jor, hor_fim_jor,
               chegada_ponto, status_escala
        FROM tb_item_map
        WHERE id_motorista = ?
        """,
        (int(id_motorista),),
    )
    if rows.empty:
        return None
    for _, row in rows.iterrows():
        id_outro = int(row["id_item"])
        if id_item_excluir is not None and id_outro == int(id_item_excluir):
            continue
        ini = (
            _as_datetime(row.get("inicio_real"))
            or _as_datetime(row.get("chegada_ponto"))
            or _as_datetime(row.get("hor_ini_jor"))
        )
        if ini is None:
            continue
        status = str(row.get("status_escala") or "").strip().upper()
        fim_o = _as_datetime(row.get("fim_real"))
        if fim_o is None and status == STATUS_ESCALA_ENCERRADA:
            fim_o = _as_datetime(row.get("baixa_em")) or _as_datetime(row.get("hor_fim_jor"))
        if fim_o is None and status != STATUS_ESCALA_ENCERRADA:
            fim_o = None  # em andamento
        elif fim_o is None:
            fim_o = _as_datetime(row.get("hor_fim_jor"))
        if _intervalos_sobrepoem(inicio, fim, ini, fim_o):
            return MapaError(
                "Intervalo sobrepõe outra escala do mesmo motorista. "
                "Ajuste o início/fim real ou dê baixa na escala anterior.",
                "conflito_sobreposicao",
            )
    return None


def _ultima_chegada_viagem(
    dal, id_item: int, id_viagem_excluir: int | None = None, data_mapa: Any = None
) -> datetime | None:
    params: list[Any] = [int(id_item)]
    sql = """
        SELECT horario_saida, horario_chegada
        FROM tb_viagem
        WHERE id_item_registro = ?
    """
    if id_viagem_excluir is not None:
        sql += " AND id_viagem <> ?"
        params.append(int(id_viagem_excluir))
    df = dal.read(sql, tuple(params))
    if df.empty:
        return None
    ultima: datetime | None = None
    for _, row in df.iterrows():
        cheg = _combinar_com_data_mapa(
            _as_datetime(row.get("horario_chegada")), data_mapa
        )
        if cheg is None:
            continue
        if ultima is None or cheg > ultima:
            ultima = cheg
    return ultima


def _frota_do_item(dal, id_item: int) -> str:
    df = dal.read(
        """
        SELECT v.numero_frota
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if df.empty:
        return str(id_item)
    return str(df.iloc[0].get("numero_frota") or id_item).strip().upper()


def _data_mapa_do_item(dal, id_item: int) -> Any:
    df = dal.read(
        """
        SELECT m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if df.empty:
        return None
    return df.iloc[0].get("data_mapa")


def _janela_ativa_escala(dal, id_item: int) -> tuple[datetime | None, datetime | None]:
    """Horários ativos da escala (início real/planejado → fim planejado/real)."""
    df = dal.read(
        """
        SELECT inicio_real, chegada_ponto, hor_ini_jor, hor_fim_jor, fim_real, baixa_em
        FROM tb_item_map
        WHERE id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if df.empty:
        return None, None
    row = df.iloc[0]
    data_mapa = _data_mapa_do_item(dal, id_item)
    inicio = _combinar_com_data_mapa(
        _as_datetime(row.get("inicio_real"))
        or _as_datetime(row.get("chegada_ponto"))
        or _as_datetime(row.get("hor_ini_jor")),
        data_mapa,
    )
    fim = _combinar_com_data_mapa(
        _as_datetime(row.get("fim_real"))
        or _as_datetime(row.get("baixa_em"))
        or _as_datetime(row.get("hor_fim_jor")),
        data_mapa,
    )
    return inicio, fim


def _viagens_sobrepoem(
    nova_saida: datetime,
    nova_chegada: datetime,
    saida_existente: datetime,
    chegada_existente: datetime,
) -> bool:
    """
    Conflito quando há interseção:
    nova_saida < chegada_existente AND nova_chegada > saida_existente.
    Limite igual (nova_saida == chegada_existente) NÃO conflita.
    """
    return nova_saida < chegada_existente and nova_chegada > saida_existente


def _erro_conflito_horarios_viagem(
    dal,
    id_item: int,
    saida: datetime,
    chegada: datetime,
    id_viagem_excluir: int | None = None,
) -> MapaError | None:
    """
    Percurso sequencial na mesma escala (mesmo id_mapa_item):
    - chegada > saida (senão 422);
    - sem interseção com qualquer viagem do item;
    - na criação, saída >= chegada da última viagem;
    - dentro da janela ativa da escala (jornada), quando definida.
    """
    if chegada <= saida:
        return MapaError(
            "A chegada deve ser posterior à saída da viagem.",
            "horario_invalido",
        )

    data_mapa = _data_mapa_do_item(dal, id_item)
    saida_n = _combinar_com_data_mapa(saida, data_mapa) or saida
    chegada_n = _combinar_com_data_mapa(chegada, data_mapa) or chegada
    if chegada_n <= saida_n:
        return MapaError(
            "A chegada deve ser posterior à saída da viagem.",
            "horario_invalido",
        )

    frota = _frota_do_item(dal, id_item)

    inicio_esc, fim_esc = _janela_ativa_escala(dal, id_item)
    if inicio_esc is not None and saida_n < inicio_esc:
        return MapaError(
            "A viagem não pode começar antes do início ativo da escala "
            f"({_format_hhmm(inicio_esc)}).",
            "conflito_horario",
        )
    if fim_esc is not None and chegada_n > fim_esc:
        return MapaError(
            "A viagem não pode terminar após o fim da jornada da escala "
            f"({_format_hhmm(fim_esc)}).",
            "conflito_horario",
        )

    params: list[Any] = [int(id_item)]
    sql = """
        SELECT id_viagem, horario_saida, horario_chegada
        FROM tb_viagem
        WHERE id_item_registro = ?
    """
    if id_viagem_excluir is not None:
        sql += " AND id_viagem <> ?"
        params.append(int(id_viagem_excluir))
    existentes = dal.read(sql, tuple(params))

    ultima_chegada: datetime | None = None
    ultima_saida: datetime | None = None
    for _, row in existentes.iterrows():
        v0 = _combinar_com_data_mapa(_as_datetime(row.get("horario_saida")), data_mapa)
        v1 = _combinar_com_data_mapa(
            _as_datetime(row.get("horario_chegada")), data_mapa
        )
        if v0 is None or v1 is None:
            continue
        if _viagens_sobrepoem(saida_n, chegada_n, v0, v1):
            return MapaError(
                f"O veículo {frota} já possui viagem entre {_format_hhmm(v0)} e "
                f"{_format_hhmm(v1)}. Informe uma saída a partir de {_format_hhmm(v1)}.",
                "conflito_horario",
            )
        if ultima_chegada is None or v1 > ultima_chegada:
            ultima_chegada = v1
            ultima_saida = v0

    # Criação: próxima saída somente a partir da última chegada
    if id_viagem_excluir is None and ultima_chegada is not None and saida_n < ultima_chegada:
        saida_ref = ultima_saida or ultima_chegada
        return MapaError(
            f"O veículo {frota} já possui viagem entre {_format_hhmm(saida_ref)} e "
            f"{_format_hhmm(ultima_chegada)}. Informe uma saída a partir de "
            f"{_format_hhmm(ultima_chegada)}.",
            "conflito_horario",
        )
    return None


def _enriquecer_campos_horas_item(item: dict[str, Any]) -> dict[str, Any]:
    """Aliases de leitura: planejado + reais + duração formatada."""
    item["inicio_jornada_planejado"] = item.get("hor_ini_jor")
    item["fim_jornada_planejado"] = item.get("hor_fim_jor")
    if item.get("fim_real") in (None, "") and item.get("baixa_em") not in (None, ""):
        item["fim_real"] = item.get("baixa_em")
    dur = item.get("duracao_trabalhada_minutos")
    try:
        if dur is not None and str(dur).strip() != "":
            item["duracao_trabalhada_hhmm"] = _format_hhmm_from_minutos(int(dur))
        else:
            item["duracao_trabalhada_hhmm"] = None
    except (TypeError, ValueError):
        item["duracao_trabalhada_hhmm"] = None
    return item


def dar_baixa_item_map(
    dal, id_item: int, payload: dict[str, Any] | None = None
) -> dict[str, Any] | MapaError:
    """
    Encerra a escala com fim real e duração trabalhadas.
    Não apaga histórico/viagens; libera veículo/motorista.
    """
    body = dict(payload or {})
    atual = dal.read(
        """
        SELECT id_item, id_motorista, id_veiculo, status_escala,
               inicio_real, chegada_ponto, hor_ini_jor, fim_real, baixa_em
        FROM tb_item_map WHERE id_item = ? LIMIT 1
        """,
        (int(id_item),),
    )
    if atual.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    row = atual.iloc[0]
    status = str(row.get("status_escala") or "").strip().upper()
    if status == STATUS_ESCALA_ENCERRADA:
        return MapaError("Esta escala já está encerrada.", "validacao")
    if status and status != STATUS_ESCALA_EM_ANDAMENTO:
        return MapaError(
            "Somente escalas em andamento podem receber baixa.",
            "validacao",
        )

    inicio = (
        _as_datetime(row.get("inicio_real"))
        or _as_datetime(row.get("chegada_ponto"))
        or _as_datetime(row.get("hor_ini_jor"))
    )
    if inicio is None:
        return MapaError(
            "Escala sem início real. Informe o início antes de dar baixa.",
            "validacao",
        )

    fim_raw = body.get("fim_real", body.get("data_hora_baixa", body.get("baixa_em")))
    if fim_raw is None or str(fim_raw).strip() == "":
        return MapaError(
            "Informe a data/hora real de encerramento (fim_real).",
            "validacao",
        )
    fim = _as_datetime(fim_raw)
    if fim is None:
        return MapaError("Data/hora de encerramento inválida.", "validacao")
    if fim < inicio:
        return MapaError(
            "O fim real não pode ser anterior ao início real.",
            "validacao",
        )

    ultima_viagem = _ultima_chegada_viagem(
        dal, int(id_item), data_mapa=_data_mapa_do_item(dal, int(id_item))
    )
    if ultima_viagem is not None and fim < ultima_viagem:
        return MapaError(
            "Não é possível dar baixa antes do fim da última viagem registrada "
            f"({ultima_viagem.strftime('%H:%M')}).",
            "validacao",
        )

    minutos = _duracao_minutos(inicio, fim)
    if minutos < 0:
        return MapaError("Duração trabalhadas inválida.", "validacao")

    motivo = str(body.get("motivo_baixa") or "").strip() or None
    if motivo and len(motivo) > 120:
        return MapaError("motivo_baixa excede 120 caracteres.", "validacao")
    obs = str(body.get("observacao_baixa") or "").strip() or None
    if obs and len(obs) > 500:
        return MapaError("observacao_baixa excede 500 caracteres.", "validacao")

    fim_txt = fim.strftime("%Y-%m-%d %H:%M:%S")
    inicio_txt = inicio.strftime("%Y-%m-%d %H:%M:%S")
    data_baixa_txt = fim.strftime("%Y-%m-%d")
    hora_baixa_txt = fim.strftime("%H:%M:%S")

    with dal.transaction():
        ok = dal.update(
            """
            UPDATE tb_item_map
            SET status_escala = ?,
                inicio_real = COALESCE(inicio_real, ?),
                fim_real = ?,
                baixa_em = ?,
                data_baixa = ?,
                hora_baixa = ?,
                motivo_baixa = ?,
                observacao_baixa = ?,
                duracao_trabalhada_minutos = ?
            WHERE id_item = ?
              AND UPPER(TRIM(status_escala)) = ?
            """,
            (
                STATUS_ESCALA_ENCERRADA,
                inicio_txt,
                fim_txt,
                fim_txt,
                data_baixa_txt,
                hora_baixa_txt,
                motivo,
                obs,
                minutos,
                int(id_item),
                STATUS_ESCALA_EM_ANDAMENTO,
            ),
        )
        if not ok:
            return MapaError(
                "Não foi possível dar baixa (escala já encerrada ou alterada).",
                "conflito_baixa",
            )
        confere = dal.read(
            """
            SELECT id_item, status_escala, fim_real, duracao_trabalhada_minutos
            FROM tb_item_map WHERE id_item = ? LIMIT 1
            """,
            (int(id_item),),
        )
        if confere.empty:
            return MapaError("Item não encontrado.", "nao_encontrado")
        st = str(confere.iloc[0].get("status_escala") or "").strip().upper()
        if st != STATUS_ESCALA_ENCERRADA:
            return MapaError(
                "Não foi possível dar baixa (conflito concorrente).",
                "conflito_baixa",
            )

    item = _item_map_detalhe(dal, int(id_item))
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def obter_banco_horas_motorista(
    dal, id_motorista: int, data_ref: date
) -> dict[str, Any] | MapaError:
    """
    Controle operacional do dia: períodos por veículo + totais.
    Não é integração de folha/RH.
    """
    mot = dal.read(
        """
        SELECT id_motorista, matricula, nome, ativo
        FROM tb_motorista WHERE id_motorista = ? LIMIT 1
        """,
        (int(id_motorista),),
    )
    if mot.empty:
        return MapaError("Motorista não encontrado.", "nao_encontrado")

    dia = data_ref.strftime("%Y-%m-%d")
    # Escalas cujo início real (ou planejado) cai no dia, ou atravessam o dia
    itens_df = dal.read(
        """
        SELECT i.*,
               v.numero_frota,
               m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_motorista = ?
        ORDER BY i.id_item
        """,
        (int(id_motorista),),
    )

    agora = datetime.now().replace(second=0, microsecond=0)
    dia_ini = datetime.combine(data_ref, datetime.min.time())
    dia_fim = datetime.combine(data_ref, datetime.max.time().replace(microsecond=0))

    encerradas: list[dict[str, Any]] = []
    em_andamento: dict[str, Any] | None = None
    alertas: list[str] = []
    intervalos_fechados: list[tuple[datetime, datetime, int]] = []

    if not itens_df.empty:
        for _, row in itens_df.iterrows():
            item = row.to_dict()
            ini = (
                _as_datetime(item.get("inicio_real"))
                or _as_datetime(item.get("chegada_ponto"))
                or _as_datetime(item.get("hor_ini_jor"))
            )
            if ini is None:
                continue
            status = str(item.get("status_escala") or "").strip().upper()
            fim = _as_datetime(item.get("fim_real")) or _as_datetime(item.get("baixa_em"))
            # Filtra escalas do dia (início no dia ou intervalo cruza o dia)
            fim_ref = fim if fim is not None else agora
            if fim_ref < dia_ini or ini > dia_fim:
                # ainda pode atravessar meia-noite do dia anterior
                if not (ini.date() == data_ref or (fim and fim.date() == data_ref) or (fim_ref >= dia_ini and ini <= dia_fim)):
                    continue
            if ini.date() != data_ref and (fim is None or fim.date() != data_ref):
                if not (ini < dia_fim and fim_ref >= dia_ini):
                    continue

            frota = str(item.get("numero_frota") or item.get("id_veiculo") or "")
            base = {
                "id_item": int(item["id_item"]),
                "idmap": int(item["idmap"]),
                "id_veiculo": int(item["id_veiculo"]),
                "numero_frota": frota,
                "inicio_real": ini.strftime("%Y-%m-%d %H:%M:%S"),
                "status_escala": status or STATUS_ESCALA_EM_ANDAMENTO,
            }

            if status == STATUS_ESCALA_ENCERRADA and fim is not None:
                dur = item.get("duracao_trabalhada_minutos")
                try:
                    minutos = int(dur) if dur is not None and str(dur).strip() != "" else _duracao_minutos(ini, fim)
                except (TypeError, ValueError):
                    minutos = _duracao_minutos(ini, fim)
                # Detecta sobreposição com já acumulados (legado)
                for a0, a1, _aid in intervalos_fechados:
                    if _intervalos_sobrepoem(ini, fim, a0, a1):
                        alertas.append(
                            f"Sobreposição detectada entre escalas (veículo {frota}). "
                            "Conferir dados legados — minutos não foram somados em duplicidade."
                        )
                        break
                else:
                    intervalos_fechados.append((ini, fim, int(item["id_item"])))
                # Soma sem duplicar: usa união simples via merge de intervalos
                base.update(
                    {
                        "fim_real": fim.strftime("%Y-%m-%d %H:%M:%S"),
                        "duracao_trabalhada_minutos": minutos,
                        "duracao_trabalhada_hhmm": _format_hhmm_from_minutos(minutos),
                    }
                )
                encerradas.append(base)
            elif status != STATUS_ESCALA_ENCERRADA:
                est = _duracao_minutos(ini, agora) if agora >= ini else 0
                base.update(
                    {
                        "fim_real": None,
                        "duracao_estimada_minutos": est,
                        "duracao_estimada_hhmm": _format_hhmm_from_minutos(est),
                        "estimativa": True,
                    }
                )
                em_andamento = base

    # Total encerrado sem duplicar sobreposições (merge intervalos)
    intervalos_fechados.sort(key=lambda x: x[0])
    merged: list[tuple[datetime, datetime]] = []
    for a0, a1, _ in intervalos_fechados:
        if not merged or a0 >= merged[-1][1]:
            merged.append((a0, a1))
        else:
            # overlap legado: estende sem somar duas vezes
            prev0, prev1 = merged[-1]
            merged[-1] = (prev0, max(prev1, a1))
            if "Sobreposição" not in " ".join(alertas):
                alertas.append(
                    "Intervalos legados sobrepostos foram unidos no total do dia."
                )

    total_encerrado = sum(_duracao_minutos(a, b) for a, b in merged)
    total_estimado = (
        int(em_andamento["duracao_estimada_minutos"]) if em_andamento else 0
    )

    # Lacunas entre escalas encerradas (informativo)
    for i in range(1, len(merged)):
        gap = _duracao_minutos(merged[i - 1][1], merged[i][0])
        if gap > 0:
            alertas.append(
                f"Lacuna de {_format_hhmm_from_minutos(gap)} entre escalas encerradas."
            )

    motorista = mot.iloc[0].to_dict()
    return {
        "controle": "operacional",
        "aviso": "Controle operacional — não é integração oficial de folha de pagamento.",
        "motorista": {
            "id_motorista": int(motorista["id_motorista"]),
            "matricula": motorista.get("matricula"),
            "nome": motorista.get("nome"),
        },
        "data": dia,
        "escalas_encerradas": encerradas,
        "escala_em_andamento": em_andamento,
        "total_minutos_encerrados": total_encerrado,
        "total_encerrado_hhmm": _format_hhmm_from_minutos(total_encerrado),
        "total_minutos_estimativa_andamento": total_estimado,
        "total_estimativa_andamento_hhmm": _format_hhmm_from_minutos(total_estimado),
        "alertas": alertas,
    }


def _validar_frota_prefixo_veiculo(
    dal, id_veiculo: int, id_linha: int
) -> MapaError | None:
    """Confere prefixo/faixa da frota com a empresa da linha."""
    lin = dal.read(
        """
        SELECT e.descricao AS empresa
        FROM tb_linha l
        INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        WHERE l.id_linha = ?
        LIMIT 1
        """,
        (int(id_linha),),
    )
    if lin.empty:
        return MapaError("Linha não encontrada.", "nao_encontrado")
    vei = dal.read(
        "SELECT numero_frota FROM tb_veiculo WHERE id_veiculo = ? LIMIT 1",
        (int(id_veiculo),),
    )
    if vei.empty:
        return MapaError("Veículo não encontrado.", "validacao")
    from .cadastros_service import CadastroError, _validar_frota_empresa

    validado = _validar_frota_empresa(
        str(vei.iloc[0]["numero_frota"] or ""),
        str(lin.iloc[0]["empresa"] or ""),
    )
    if isinstance(validado, CadastroError):
        return MapaError(validado.mensagem, validado.codigo)
    return None


def _resolver_id_linha_item(dal, payload: dict[str, Any]) -> int | MapaError:
    """Linha obrigatória no item (PK ativa)."""
    raw = payload.get("id_linha")
    if raw is None or str(raw).strip() == "":
        return MapaError("Linha é obrigatória.", "validacao")
    try:
        id_linha = int(raw)
    except (TypeError, ValueError):
        return MapaError("Linha inválida.", "validacao")
    df = dal.read(
        "SELECT id_linha, id_empresa FROM tb_linha WHERE id_linha = ? AND ativo = 1",
        (id_linha,),
    )
    if df.empty:
        return MapaError("Linha não encontrada.", "nao_encontrado")
    return int(df.iloc[0]["id_linha"])


def _validar_veiculo_empresa_da_linha(
    dal, id_veiculo: int, id_linha: int
) -> MapaError | None:
    lin = dal.read(
        "SELECT id_empresa FROM tb_linha WHERE id_linha = ?",
        (int(id_linha),),
    )
    if lin.empty:
        return MapaError("Linha não encontrada.", "nao_encontrado")
    id_emp_linha = int(lin.iloc[0]["id_empresa"])

    vei = dal.read(
        "SELECT id_veiculo, id_empresa, ativo FROM tb_veiculo WHERE id_veiculo = ?",
        (int(id_veiculo),),
    )
    if vei.empty:
        return MapaError("Veículo não encontrado.", "validacao")
    if int(vei.iloc[0].get("ativo") or 0) not in (1, True):
        return MapaError("Veículo está inativo.", "validacao")
    id_emp_vei = vei.iloc[0]["id_empresa"]
    if id_emp_vei is not None and str(id_emp_vei) not in ("", "None", "nan"):
        if int(id_emp_vei) != id_emp_linha:
            return MapaError(
                "Veículo não pertence à empresa da linha.",
                "validacao",
            )
    return None


def _exigir_horarios_item(
    payload: dict[str, Any], data_mapa: Any
) -> tuple[Any, Any, Any] | MapaError:
    """Início, fim e chegada obrigatórios no item."""
    for key, label in (
        ("hor_ini_jor", "Início de jornada"),
        ("hor_fim_jor", "Fim de jornada"),
        ("chegada_ponto", "Chegada no ponto"),
    ):
        raw = payload.get(key)
        if raw is None or str(raw).strip() == "":
            return MapaError(f"{label} é obrigatório.", "validacao")
    horarios = _normalizar_horarios_item(payload, data_mapa)
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios
    if hor_ini is None or hor_fim is None or chegada is None:
        return MapaError(
            "Início, fim de jornada e chegada ao ponto são obrigatórios.",
            "validacao",
        )
    if hor_ini >= hor_fim:
        return MapaError("Início da jornada deve ser anterior ao fim.", "validacao")
    return hor_ini, hor_fim, chegada


def criar_item_map(
    dal, id_registro: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    mapa = dal.read(
        "SELECT id_registro, data FROM tb_map WHERE id_registro = ?",
        (id_registro,),
    )
    if mapa.empty:
        return MapaError("MAPA não encontrado.", "nao_encontrado")

    id_linha = _resolver_id_linha_item(dal, payload)
    if isinstance(id_linha, MapaError):
        return id_linha

    id_veiculo = _resolver_id_veiculo(dal, payload)
    if isinstance(id_veiculo, MapaError):
        return id_veiculo

    err_emp = _validar_veiculo_empresa_da_linha(dal, int(id_veiculo), int(id_linha))
    if err_emp is not None:
        return err_emp

    err_frota = _validar_frota_prefixo_veiculo(dal, int(id_veiculo), int(id_linha))
    if err_frota is not None:
        return err_frota

    id_motorista = _resolver_id_motorista(dal, payload)
    if isinstance(id_motorista, MapaError):
        return id_motorista

    data_mapa = mapa.iloc[0]["data"]
    horarios = _exigir_horarios_item(payload, data_mapa)
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios
    inicio_real = _resolver_inicio_real_item(payload, chegada, hor_ini)

    try:
        with dal.transaction():
            conflito = _erro_veiculo_ja_alocado(dal, id_registro, int(id_veiculo))
            if conflito is not None:
                return conflito

            conflito_mot = _erro_motorista_ja_alocado(
                dal, id_registro, int(id_motorista)
            )
            if conflito_mot is not None:
                return conflito_mot

            sobre = _erro_sobreposicao_motorista(
                dal, int(id_motorista), inicio_real, None
            )
            if sobre is not None:
                return sobre

            ok = dal.create(
                """
                INSERT INTO tb_item_map (
                    idmap, id_linha, id_veiculo, id_motorista,
                    hor_ini_jor, hor_fim_jor, chegada_ponto,
                    inicio_real, fim_real, status_escala, baixa_em,
                    motivo_baixa, observacao_baixa, duracao_trabalhada_minutos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, NULL, NULL)
                """,
                (
                    id_registro,
                    int(id_linha),
                    int(id_veiculo),
                    int(id_motorista),
                    hor_ini,
                    hor_fim,
                    chegada,
                    inicio_real.strftime("%Y-%m-%d %H:%M:%S"),
                    STATUS_ESCALA_EM_ANDAMENTO,
                ),
            )
            if not ok:
                conflito = _erro_veiculo_ja_alocado(
                    dal, id_registro, int(id_veiculo)
                )
                if conflito is not None:
                    return conflito
                conflito_mot = _erro_motorista_ja_alocado(
                    dal, id_registro, int(id_motorista)
                )
                if conflito_mot is not None:
                    return conflito_mot
                return MapaError(
                    "Falha ao gravar o registro no banco (verifique horários e vínculos).",
                    "persistencia",
                )

            row = dal.read(
                "SELECT MAX(id_item) AS id_item FROM tb_item_map WHERE idmap = ?",
                (id_registro,),
            )
            id_item = int(row.iloc[0]["id_item"])
    except Exception:
        return MapaError(
            "Falha ao gravar o registro no banco (verifique horários e vínculos).",
            "persistencia",
        )

    item = _item_map_detalhe(dal, id_item)
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def atualizar_item_map(
    dal, id_item: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    atual = dal.read(
        """
        SELECT i.id_item, i.idmap, i.status_escala, m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if atual.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    status = str(atual.iloc[0].get("status_escala") or "").strip().upper()
    if status == STATUS_ESCALA_ENCERRADA:
        return MapaError(
            "Esta escala foi encerrada e não pode ser alterada.",
            "validacao",
        )

    idmap = int(atual.iloc[0]["idmap"])

    id_linha = _resolver_id_linha_item(dal, payload)
    if isinstance(id_linha, MapaError):
        return id_linha

    id_veiculo = _resolver_id_veiculo(dal, payload)
    if isinstance(id_veiculo, MapaError):
        return id_veiculo

    err_emp = _validar_veiculo_empresa_da_linha(dal, int(id_veiculo), int(id_linha))
    if err_emp is not None:
        return err_emp

    err_frota = _validar_frota_prefixo_veiculo(dal, int(id_veiculo), int(id_linha))
    if err_frota is not None:
        return err_frota

    id_motorista = _resolver_id_motorista(dal, payload)
    if isinstance(id_motorista, MapaError):
        return id_motorista

    horarios = _exigir_horarios_item(payload, atual.iloc[0]["data_mapa"])
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios
    inicio_real = _resolver_inicio_real_item(payload, chegada, hor_ini)

    try:
        with dal.transaction():
            conflito = _erro_veiculo_ja_alocado(
                dal, idmap, int(id_veiculo), id_item_excluir=id_item
            )
            if conflito is not None:
                return conflito

            conflito_mot = _erro_motorista_ja_alocado(
                dal, idmap, int(id_motorista), id_item_excluir=id_item
            )
            if conflito_mot is not None:
                return conflito_mot

            sobre = _erro_sobreposicao_motorista(
                dal,
                int(id_motorista),
                inicio_real,
                None,
                id_item_excluir=id_item,
            )
            if sobre is not None:
                return sobre

            ok = dal.update(
                """
                UPDATE tb_item_map
                SET id_linha = ?, id_veiculo = ?, id_motorista = ?,
                    hor_ini_jor = ?, hor_fim_jor = ?, chegada_ponto = ?,
                    inicio_real = COALESCE(?, inicio_real),
                    status_escala = ?
                WHERE id_item = ?
                  AND UPPER(TRIM(status_escala)) = ?
                """,
                (
                    int(id_linha),
                    int(id_veiculo),
                    int(id_motorista),
                    hor_ini,
                    hor_fim,
                    chegada,
                    inicio_real.strftime("%Y-%m-%d %H:%M:%S"),
                    STATUS_ESCALA_EM_ANDAMENTO,
                    id_item,
                    STATUS_ESCALA_EM_ANDAMENTO,
                ),
            )
            if not ok:
                conflito = _erro_veiculo_ja_alocado(
                    dal, idmap, int(id_veiculo), id_item_excluir=id_item
                )
                if conflito is not None:
                    return conflito
                conflito_mot = _erro_motorista_ja_alocado(
                    dal, idmap, int(id_motorista), id_item_excluir=id_item
                )
                if conflito_mot is not None:
                    return conflito_mot
                return MapaError("Falha ao atualizar item.", "persistencia")
    except Exception:
        return MapaError("Falha ao atualizar item.", "persistencia")

    item = _item_map_detalhe(dal, id_item)
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def _coerce_mapa_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = _parse_date(value)
    if isinstance(parsed, MapaError):
        return None
    return parsed


def _parse_horario_item(
    value: Any, data_mapa: Any, campo: str
) -> datetime | None | MapaError:
    """Aceita datetime completo, HH:MM (usa data do MAPA) ou vazio → NULL."""
    if value is None:
        return None
    texto = str(value).strip()
    if not texto or texto.lower() in ("null", "none"):
        return None

    parsed = _parse_datetime_optional(texto)
    if not isinstance(parsed, MapaError):
        return parsed

    m = re.fullmatch(r"(\d{2}):(\d{2})(?::(\d{2}))?", texto)
    if m:
        base = _coerce_mapa_date(data_mapa)
        if base is None:
            return MapaError(
                f"Data do MAPA inválida para gravar {campo}.",
                "validacao",
            )
        hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        if hh > 23 or mm > 59 or ss > 59:
            return MapaError(f"{campo} inválido.", "validacao")
        return datetime(base.year, base.month, base.day, hh, mm, ss)

    return MapaError(f"{campo} inválido.", "validacao")


def _normalizar_horarios_item(
    payload: dict[str, Any],
    data_mapa: Any = None,
) -> tuple[datetime | None, datetime | None, datetime | None] | MapaError:
    """Converte horários do item; string vazia vira NULL (MariaDB rejeita '')."""
    hor_ini = _parse_horario_item(payload.get("hor_ini_jor"), data_mapa, "Início de jornada")
    if isinstance(hor_ini, MapaError):
        return hor_ini
    hor_fim = _parse_horario_item(payload.get("hor_fim_jor"), data_mapa, "Fim de jornada")
    if isinstance(hor_fim, MapaError):
        return hor_fim
    chegada = _parse_horario_item(payload.get("chegada_ponto"), data_mapa, "Chegada no ponto")
    if isinstance(chegada, MapaError):
        return chegada
    return hor_ini, hor_fim, chegada


def _item_map_detalhe(dal, id_item: int) -> dict[str, Any] | None:
    item_df = dal.read(
        """
        SELECT i.*,
               v.numero_frota, v.placa,
               l.codigo_linha, l.descricao AS linha,
               e.id_empresa, e.descricao AS empresa,
               mot.nome AS motorista, mot.matricula AS matricula_motorista
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_linha l ON l.id_linha = i.id_linha
        INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if item_df.empty:
        return None
    item = item_df.iloc[0].to_dict()
    item["id_mapa_item"] = int(item["id_item"])
    st = str(item.get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO).strip().upper()
    item["status_escala"] = st or STATUS_ESCALA_EM_ANDAMENTO
    item["viagens"] = []
    return _enriquecer_campos_horas_item(item)


def excluir_item_map(dal, id_item: int) -> MapaError | None:
    dal.delete("DELETE FROM tb_viagem WHERE id_item_registro = ?", (id_item,))
    ok = dal.delete("DELETE FROM tb_item_map WHERE id_item = ?", (id_item,))
    if not ok:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return None


def _normalizar_placa_hhmm(value: Any) -> str | None | MapaError:
    """Campo Placa da UI de viagem: obrigatoriamente HH:MM (5 caracteres) ou vazio."""
    if value is None:
        return None
    texto = str(value).strip()
    if not texto or texto in ("—", "-"):
        return None
    # Aceita HHMM digitado sem ':' e normaliza
    digits = "".join(ch for ch in texto if ch.isdigit())
    if len(digits) == 4 and ":" not in texto:
        texto = f"{digits[:2]}:{digits[2:]}"
    if not re.fullmatch(r"\d{2}:\d{2}", texto):
        return MapaError("Placa deve estar no formato HH:MM.", "validacao")
    hh, mm = int(texto[:2]), int(texto[3:])
    if hh > 23 or mm > 59:
        return MapaError("Placa inválida (HH:MM).", "validacao")
    return texto


def _validar_item_apto_viagem(
    dal,
    id_item: int,
    payload: dict[str, Any] | None = None,
) -> MapaError | None:
    """
    Viagem exige item existente com veículo + motorista.
    Não associa viagem só por frota/prefixo de veículo.
    """
    body = payload or {}
    # Aceita id_mapa_item / id_item no body — deve bater com a rota.
    for key in ("id_mapa_item", "id_item", "id_item_registro"):
        raw = body.get(key)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            if int(raw) != int(id_item):
                return MapaError(
                    "id_mapa_item não corresponde ao item da viagem.",
                    "validacao",
                )
        except (TypeError, ValueError):
            return MapaError("id_mapa_item inválido.", "validacao")

    item = dal.read(
        """
        SELECT i.id_item, i.idmap, i.id_veiculo, i.id_motorista, i.status_escala
        FROM tb_item_map i
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if item.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    status = str(item.iloc[0].get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO)
    status = status.strip().upper() or STATUS_ESCALA_EM_ANDAMENTO
    if status == STATUS_ESCALA_ENCERRADA:
        return MapaError(
            "Esta escala recebeu baixa e não aceita novas viagens.",
            "escala_encerrada",
        )
    if status != STATUS_ESCALA_EM_ANDAMENTO:
        return MapaError(
            "Somente escalas em andamento podem registrar viagens.",
            "validacao",
        )

    idmap_raw = body.get("idmap", body.get("id_registro", body.get("id_mapa")))
    if idmap_raw is not None and str(idmap_raw).strip() != "":
        try:
            if int(idmap_raw) != int(item.iloc[0]["idmap"]):
                return MapaError(
                    "Item não pertence ao MAPA informado.",
                    "validacao",
                )
        except (TypeError, ValueError):
            return MapaError("MAPA inválido.", "validacao")

    id_veiculo = item.iloc[0]["id_veiculo"]
    id_motorista = item.iloc[0]["id_motorista"]
    if id_veiculo is None or str(id_veiculo).strip() in ("", "None", "nan"):
        return MapaError(
            "Item sem veículo vinculado. Vincule o motorista/veículo antes de registrar viagens.",
            "validacao",
        )
    try:
        if int(id_veiculo) <= 0:
            return MapaError(
                "Item sem veículo vinculado. Vincule o motorista/veículo antes de registrar viagens.",
                "validacao",
            )
    except (TypeError, ValueError):
        return MapaError(
            "Item sem veículo vinculado. Vincule o motorista/veículo antes de registrar viagens.",
            "validacao",
        )

    if id_motorista is None or str(id_motorista).strip() in ("", "None", "nan"):
        return MapaError(
            "Item sem motorista vinculado. Vincule o motorista antes de registrar viagens.",
            "validacao",
        )
    try:
        if int(id_motorista) <= 0:
            return MapaError(
                "Item sem motorista vinculado. Vincule o motorista antes de registrar viagens.",
                "validacao",
            )
    except (TypeError, ValueError):
        return MapaError(
            "Item sem motorista vinculado. Vincule o motorista antes de registrar viagens.",
            "validacao",
        )
    return None


def _horarios_viagem_do_payload(
    dal, id_item: int, payload: dict[str, Any]
) -> tuple[datetime, datetime, str | None, int, int, Any] | MapaError:
    """Resolve saída/chegada/placa(HH:MM) e quantidades — sem trocar campos."""
    apto = _validar_item_apto_viagem(dal, id_item, payload)
    if apto is not None:
        return apto

    item = dal.read(
        """
        SELECT i.id_item, m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if item.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    data_mapa = item.iloc[0]["data_mapa"]
    # Campos distintos: nao misturar placa com saida/chegada
    saida = _parse_horario_item(payload.get("horario_saida"), data_mapa, "Saída da viagem")
    if isinstance(saida, MapaError):
        return saida
    if saida is None:
        return MapaError("Saída da viagem é obrigatória.", "validacao")
    chegada = _parse_horario_item(
        payload.get("horario_chegada"), data_mapa, "Chegada da viagem"
    )
    if isinstance(chegada, MapaError):
        return chegada
    if chegada is None:
        return MapaError("Chegada da viagem é obrigatória.", "validacao")

    placa = _normalizar_placa_hhmm(payload.get("placa"))
    if isinstance(placa, MapaError):
        return placa

    qtd_pas = payload.get("qtd_passageiro", payload.get("qtd_pas_ida", 0))
    qtd_ida = qtd_pas
    qtd_volta = payload.get("qtd_pas_volta", 0)
    try:
        qtd_ida = max(0, int(qtd_ida))
        qtd_volta = max(0, int(qtd_volta))
    except (TypeError, ValueError):
        return MapaError("Quantidade de passageiros inválida.", "validacao")

    return saida, chegada, placa, qtd_ida, qtd_volta, payload.get("intervalo")


def criar_viagem(
    dal, id_item: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    body = dict(payload or {})
    # Obrigatório no body: vínculo explícito ao item (não só frota/prefixo).
    raw_mapa_item = body.get("id_mapa_item", body.get("id_item"))
    if raw_mapa_item is None or str(raw_mapa_item).strip() == "":
        return MapaError(
            "id_mapa_item é obrigatório para criar a viagem.",
            "validacao",
        )
    try:
        if int(raw_mapa_item) != int(id_item):
            return MapaError(
                "id_mapa_item não corresponde ao item da viagem.",
                "validacao",
            )
    except (TypeError, ValueError):
        return MapaError("id_mapa_item inválido.", "validacao")
    body["id_mapa_item"] = int(id_item)
    body["id_item"] = int(id_item)

    horarios = _horarios_viagem_do_payload(dal, id_item, body)
    if isinstance(horarios, MapaError):
        return horarios
    saida, chegada, placa, qtd_ida, qtd_volta, intervalo = horarios

    conflito = _erro_conflito_horarios_viagem(dal, id_item, saida, chegada)
    if conflito is not None:
        return conflito

    ok = dal.create(
        """
        INSERT INTO tb_viagem (
            id_item_registro, horario_saida, horario_chegada, placa,
            intervalo, qtd_pas_ida, qtd_pas_volta
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_item,
            saida.strftime("%Y-%m-%d %H:%M:%S"),
            chegada.strftime("%Y-%m-%d %H:%M:%S"),
            placa,
            intervalo,
            qtd_ida,
            qtd_volta,
        ),
    )
    if not ok:
        return MapaError("Falha ao criar viagem.", "persistencia")

    row = dal.read(
        "SELECT MAX(id_viagem) AS id_viagem FROM tb_viagem WHERE id_item_registro = ?",
        (id_item,),
    )
    id_viagem = int(row.iloc[0]["id_viagem"])
    viagem_df = dal.read("SELECT * FROM tb_viagem WHERE id_viagem = ?", (id_viagem,))
    out = viagem_df.iloc[0].to_dict()
    out["id_mapa_item"] = int(id_item)
    return out


def atualizar_viagem(
    dal, id_viagem: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    atual = dal.read(
        "SELECT id_viagem, id_item_registro FROM tb_viagem WHERE id_viagem = ?",
        (id_viagem,),
    )
    if atual.empty:
        return MapaError("Viagem não encontrada.", "nao_encontrada")

    id_item = int(atual.iloc[0]["id_item_registro"])
    horarios = _horarios_viagem_do_payload(dal, id_item, payload)
    if isinstance(horarios, MapaError):
        return horarios
    saida, chegada, placa, qtd_ida, qtd_volta, intervalo = horarios

    conflito = _erro_conflito_horarios_viagem(
        dal, id_item, saida, chegada, id_viagem_excluir=int(id_viagem)
    )
    if conflito is not None:
        return conflito

    ok = dal.update(
        """
        UPDATE tb_viagem
        SET horario_saida = ?, horario_chegada = ?, placa = ?, intervalo = ?,
            qtd_pas_ida = ?, qtd_pas_volta = ?
        WHERE id_viagem = ?
        """,
        (
            saida.strftime("%Y-%m-%d %H:%M:%S"),
            chegada.strftime("%Y-%m-%d %H:%M:%S"),
            placa,
            intervalo,
            qtd_ida,
            qtd_volta,
            id_viagem,
        ),
    )
    if not ok:
        return MapaError("Falha ao atualizar viagem.", "persistencia")

    viagem_df = dal.read("SELECT * FROM tb_viagem WHERE id_viagem = ?", (id_viagem,))
    if viagem_df.empty:
        return MapaError("Viagem não encontrada.", "nao_encontrada")
    return viagem_df.iloc[0].to_dict()


def excluir_viagem(dal, id_viagem: int) -> MapaError | None:
    ok = dal.delete("DELETE FROM tb_viagem WHERE id_viagem = ?", (id_viagem,))
    if not ok:
        return MapaError("Viagem não encontrada.", "nao_encontrada")
    return None


def listar_cadastros_mestres(dal) -> dict[str, list[dict[str, Any]]]:
    """RF-MAP-RN-004 — somente registros ativos."""
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


def _rows(dal, sql: str) -> list[dict[str, Any]]:
    df = dal.read(sql)
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    # Normaliza tipos numpy/pandas para JSON (ids e flags).
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
