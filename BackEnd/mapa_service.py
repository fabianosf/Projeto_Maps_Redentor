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
        viagens_df = dal.read(
            """
            SELECT * FROM tb_viagem
            WHERE id_item_registro = ?
            ORDER BY id_viagem
            """,
            (id_item,),
        )
        item["viagens"] = (
            viagens_df.to_dict(orient="records") if not viagens_df.empty else []
        )
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
    """UNIQUE (idmap, id_veiculo) — mensagem estável antes/depois do DML."""
    if id_item_excluir is None:
        existe = dal.read(
            "SELECT id_item FROM tb_item_map WHERE idmap = ? AND id_veiculo = ?",
            (idmap, int(id_veiculo)),
        )
    else:
        existe = dal.read(
            """
            SELECT id_item FROM tb_item_map
            WHERE idmap = ? AND id_veiculo = ? AND id_item <> ?
            """,
            (idmap, int(id_veiculo), int(id_item_excluir)),
        )
    if not existe.empty:
        return MapaError(
            "Este carro já está alocado neste MAPA.",
            "conflito_veiculo",
        )
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

    id_motorista = _resolver_id_motorista(dal, payload)
    if isinstance(id_motorista, MapaError):
        return id_motorista

    conflito = _erro_veiculo_ja_alocado(dal, id_registro, int(id_veiculo))
    if conflito is not None:
        return conflito

    data_mapa = mapa.iloc[0]["data"]
    horarios = _exigir_horarios_item(payload, data_mapa)
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios

    ok = dal.create(
        """
        INSERT INTO tb_item_map (
            idmap, id_linha, id_veiculo, id_motorista,
            hor_ini_jor, hor_fim_jor, chegada_ponto
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_registro,
            int(id_linha),
            int(id_veiculo),
            int(id_motorista),
            hor_ini,
            hor_fim,
            chegada,
        ),
    )
    if not ok:
        conflito = _erro_veiculo_ja_alocado(dal, id_registro, int(id_veiculo))
        if conflito is not None:
            return conflito
        return MapaError(
            "Falha ao gravar o registro no banco (verifique horários e vínculos).",
            "persistencia",
        )

    row = dal.read(
        "SELECT MAX(id_item) AS id_item FROM tb_item_map WHERE idmap = ?",
        (id_registro,),
    )
    id_item = int(row.iloc[0]["id_item"])
    item = _item_map_detalhe(dal, id_item)
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def atualizar_item_map(
    dal, id_item: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    atual = dal.read(
        """
        SELECT i.id_item, i.idmap, m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if atual.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

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

    id_motorista = _resolver_id_motorista(dal, payload)
    if isinstance(id_motorista, MapaError):
        return id_motorista

    conflito = _erro_veiculo_ja_alocado(
        dal, idmap, int(id_veiculo), id_item_excluir=id_item
    )
    if conflito is not None:
        return conflito

    horarios = _exigir_horarios_item(payload, atual.iloc[0]["data_mapa"])
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios

    ok = dal.update(
        """
        UPDATE tb_item_map
        SET id_linha = ?, id_veiculo = ?, id_motorista = ?,
            hor_ini_jor = ?, hor_fim_jor = ?, chegada_ponto = ?
        WHERE id_item = ?
        """,
        (
            int(id_linha),
            int(id_veiculo),
            int(id_motorista),
            hor_ini,
            hor_fim,
            chegada,
            id_item,
        ),
    )
    if not ok:
        conflito = _erro_veiculo_ja_alocado(
            dal, idmap, int(id_veiculo), id_item_excluir=id_item
        )
        if conflito is not None:
            return conflito
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
    item["viagens"] = []
    return item


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


def _horarios_viagem_do_payload(
    dal, id_item: int, payload: dict[str, Any]
) -> tuple[datetime, datetime, str | None, int, int, Any] | MapaError:
    """Resolve saída/chegada/placa(HH:MM) e quantidades — sem trocar campos."""
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
    horarios = _horarios_viagem_do_payload(dal, id_item, payload)
    if isinstance(horarios, MapaError):
        return horarios
    saida, chegada, placa, qtd_ida, qtd_volta, intervalo = horarios

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
    return viagem_df.iloc[0].to_dict()


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
