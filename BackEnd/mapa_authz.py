# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Autorização centralizada de MAPA (P1 — Admin / Inspetor / Despachante)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from .auth_service import UsuarioAuth
from .auditoria_service import registrar_acesso_negado
from .constants import PERFIL_ADMIN, PERFIL_DESPACHANTE, PERFIL_INSPETOR


ModoAcesso = Literal["leitura", "escrita"]


@dataclass(frozen=True)
class AuthzError:
    mensagem: str
    codigo: str = "perfil_negado"
    status: int = 403


def _row(dal, sql: str, values: tuple[Any, ...] | None = None) -> Optional[dict[str, Any]]:
    df = dal.read(sql, values) if values is not None else dal.read(sql)
    if df is None or df.empty:
        return None
    return df.iloc[0].to_dict()


def carregar_mapa_authz(dal, id_registro: int) -> Optional[dict[str, Any]]:
    """Cabeçalho mínimo para checagem de escopo/responsabilidade."""
    sql_full = """
        SELECT m.id_registro, m.id_usuario, m.id_responsavel, m.id_turno, m.id_empresa,
               m.id_linha, m.data,
               COALESCE(m.id_responsavel, m.id_usuario) AS responsavel_efetivo
        FROM tb_map m
        WHERE m.id_registro = ?
        LIMIT 1
        """
    sql_base = """
        SELECT m.id_registro, m.id_usuario, m.id_turno, m.id_empresa,
               m.id_linha, m.data,
               m.id_usuario AS responsavel_efetivo
        FROM tb_map m
        WHERE m.id_registro = ?
        LIMIT 1
        """
    try:
        return _row(dal, sql_full, (int(id_registro),))
    except Exception:
        return _row(dal, sql_base, (int(id_registro),))


def carregar_item_authz(dal, id_item: int) -> Optional[dict[str, Any]]:
    sql_full = """
        SELECT i.id_item, i.idmap, i.id_linha, i.id_veiculo, i.id_motorista,
               i.status_escala, m.id_usuario, m.id_responsavel, m.id_turno, m.id_empresa,
               COALESCE(m.id_responsavel, m.id_usuario) AS responsavel_efetivo,
               l.id_empresa AS id_empresa_linha
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        LEFT JOIN tb_linha l ON l.id_linha = i.id_linha
        WHERE i.id_item = ?
        LIMIT 1
        """
    sql_base = """
        SELECT i.id_item, i.idmap, i.id_linha, i.id_veiculo, i.id_motorista,
               i.status_escala, m.id_usuario, m.id_turno, m.id_empresa,
               m.id_usuario AS responsavel_efetivo,
               l.id_empresa AS id_empresa_linha
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        LEFT JOIN tb_linha l ON l.id_linha = i.id_linha
        WHERE i.id_item = ?
        LIMIT 1
        """
    try:
        return _row(dal, sql_full, (int(id_item),))
    except Exception:
        return _row(dal, sql_base, (int(id_item),))


def _empresa_mapa(mapa: dict[str, Any]) -> Optional[int]:
    for key in ("id_empresa", "id_empresa_linha"):
        val = mapa.get(key)
        if val is not None and str(val).strip() not in ("", "None"):
            try:
                return int(val)
            except (TypeError, ValueError):
                pass
    return None


def _inspetor_no_escopo(usuario: UsuarioAuth, mapa: dict[str, Any]) -> bool:
    """Inspetor: local/empresa/turno do usuário devem cobrir o MAPA."""
    # Turno
    if usuario.id_turno is not None and mapa.get("id_turno") is not None:
        try:
            if int(usuario.id_turno) != int(mapa["id_turno"]):
                return False
        except (TypeError, ValueError):
            return False
    # Empresa do MAPA (cabeçalho ou linha do item)
    emp_mapa = _empresa_mapa(mapa)
    if usuario.id_empresa is not None and emp_mapa is not None:
        try:
            if int(usuario.id_empresa) != int(emp_mapa):
                return False
        except (TypeError, ValueError):
            return False
    # Local: se o usuário tem local fixo, exige que alguma linha do MAPA
    # compartilhe origem/destino com esse local (quando houver itens).
    # Sem itens ainda, libera criação se empresa/turno ok.
    if usuario.id_local is not None and mapa.get("id_registro") is not None:
        # Escopo de local é validado na criação de item; no cabeçalho sem itens, ok.
        pass
    return True


def _despachante_pode_escrever(usuario: UsuarioAuth, mapa: dict[str, Any]) -> bool:
    try:
        responsavel = int(mapa.get("responsavel_efetivo") or mapa.get("id_usuario") or 0)
    except (TypeError, ValueError):
        return False
    return responsavel == int(usuario.id_usuario)


def _despachante_pode_ler(usuario: UsuarioAuth, mapa: dict[str, Any]) -> bool:
    if _despachante_pode_escrever(usuario, mapa):
        return True
    return bool(getattr(usuario, "permite_leitura_mapas_outros", False))


def autorizar_mapa(
    dal,
    usuario: UsuarioAuth,
    id_registro: int,
    *,
    modo: ModoAcesso = "escrita",
    auditar_negado: bool = True,
) -> Optional[AuthzError]:
    """Retorna AuthzError se negado; None se permitido."""
    if usuario.codigo_perfil == PERFIL_ADMIN:
        return None

    mapa = carregar_mapa_authz(dal, id_registro)
    if mapa is None:
        return AuthzError("MAPA não encontrado.", "nao_encontrado", 404)

    if usuario.codigo_perfil == PERFIL_INSPETOR:
        if not _inspetor_no_escopo(usuario, mapa):
            if auditar_negado:
                registrar_acesso_negado(
                    dal,
                    entidade="mapa",
                    id_entidade=id_registro,
                    id_executor=usuario.id_usuario,
                    perfil_executor=usuario.codigo_perfil,
                    motivo=f"Inspetor fora do escopo ({modo})",
                )
            return AuthzError(
                "Operação fora do escopo autorizado (local/empresa/turno).",
                "escopo_negado",
                403,
            )
        return None

    if usuario.codigo_perfil == PERFIL_DESPACHANTE:
        ok = (
            _despachante_pode_escrever(usuario, mapa)
            if modo == "escrita"
            else _despachante_pode_ler(usuario, mapa)
        )
        if not ok:
            if auditar_negado:
                registrar_acesso_negado(
                    dal,
                    entidade="mapa",
                    id_entidade=id_registro,
                    id_executor=usuario.id_usuario,
                    perfil_executor=usuario.codigo_perfil,
                    motivo=f"Despachante sem responsabilidade ({modo})",
                )
            return AuthzError(
                "Você só pode operar MAPAS sob sua responsabilidade.",
                "responsabilidade_negada",
                403,
            )
        return None

    if auditar_negado:
        registrar_acesso_negado(
            dal,
            entidade="mapa",
            id_entidade=id_registro,
            id_executor=usuario.id_usuario,
            perfil_executor=usuario.codigo_perfil,
            motivo="Perfil sem acesso a MAPA",
        )
    return AuthzError("Operação não autorizada.", "perfil_negado", 403)


def autorizar_item(
    dal,
    usuario: UsuarioAuth,
    id_item: int,
    *,
    modo: ModoAcesso = "escrita",
) -> Optional[AuthzError]:
    item = carregar_item_authz(dal, id_item)
    if item is None:
        return AuthzError("Item não encontrado.", "nao_encontrado", 404)
    # Injeta empresa da linha no dict de mapa
    mapa_like = dict(item)
    if mapa_like.get("id_empresa") is None:
        mapa_like["id_empresa"] = item.get("id_empresa_linha")
    # Reusa lógica via idmap
    return autorizar_mapa(
        dal, usuario, int(item["idmap"]), modo=modo, auditar_negado=True
    )


def transferir_responsavel(
    dal,
    *,
    id_registro: int,
    id_novo_responsavel: int,
    executor: UsuarioAuth,
    motivo: str,
) -> Optional[AuthzError]:
    """Somente Admin (ou futuro fluxo autorizado) transfere responsabilidade."""
    if executor.codigo_perfil != PERFIL_ADMIN:
        return AuthzError(
            "Somente Administrador pode transferir a responsabilidade do MAPA.",
            "perfil_negado",
            403,
        )
    motivo_limpo = (motivo or "").strip()
    if not motivo_limpo:
        return AuthzError("Informe o motivo da transferência.", "validacao", 400)

    mapa = carregar_mapa_authz(dal, id_registro)
    if mapa is None:
        return AuthzError("MAPA não encontrado.", "nao_encontrado", 404)

    dest = _row(
        dal,
        """
        SELECT u.id_usuario, u.ativo, p.codigo_perfil
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.id_usuario = ?
        LIMIT 1
        """,
        (int(id_novo_responsavel),),
    )
    if dest is None or not bool(dest.get("ativo")):
        return AuthzError("Novo responsável inválido ou inativo.", "validacao", 400)
    if int(dest["codigo_perfil"]) not in (
        PERFIL_ADMIN,
        PERFIL_DESPACHANTE,
        PERFIL_INSPETOR,
    ):
        return AuthzError("Perfil do responsável inválido para MAPA.", "validacao", 400)

    antes = {"id_responsavel": mapa.get("responsavel_efetivo")}
    ok = dal.update(
        "UPDATE tb_map SET id_responsavel = ? WHERE id_registro = ?",
        (int(id_novo_responsavel), int(id_registro)),
    )
    if not ok:
        return AuthzError("Falha ao transferir responsabilidade.", "persistencia", 500)

    from .auditoria_service import registrar_auditoria

    registrar_auditoria(
        dal,
        entidade="mapa",
        acao="transferir",
        id_entidade=id_registro,
        id_executor=executor.id_usuario,
        perfil_executor=executor.codigo_perfil,
        valores_antes=antes,
        valores_depois={"id_responsavel": int(id_novo_responsavel)},
        motivo=motivo_limpo,
    )
    return None
