# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Cadastro de usuários — RF-RN-013, RF-RN-014, RF-RN-015."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

from .auth_service import hash_senha
from .constants import PERFIL_DESPACHANTE, gerar_senha_provisoria
from .erp_service import ErpError, anexar_foto_erp, consultar_funcionario_erp, matricula_existe_erp
from .matricula_validation import matricula_valida

logger = logging.getLogger(__name__)

_NOME_ALFANUM = re.compile(r"^[A-Za-zÀ-ÿ0-9\s]+$")
NOME_MAX_LENGTH = 50
MSG_MATRICULA_INVALIDA = "Matrícula deve ser numérica com no máximo 5 dígitos."
MSG_NOME_INVALIDO = "Nome deve ser alfanumérico (letras, números e espaços)."
MSG_NOME_TAMANHO = f"Nome deve ter no máximo {NOME_MAX_LENGTH} caracteres."
MSG_NAO_ENCONTRADA_RH = "Matrícula não encontrada no RH."

_SELECT_USUARIO = """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               u.id_empresa, u.id_turno, u.id_local,
               p.id_perfil, p.codigo_perfil, p.descricao AS perfil_descricao
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
"""


@dataclass(frozen=True)
class ServiceError:
    mensagem: str
    codigo: str = "erro_negocio"


def _perfil_id_por_codigo(dal, codigo_perfil: int) -> Optional[int]:
    df = dal.read(
        "SELECT id_perfil FROM tb_perfil WHERE codigo_perfil = ?",
        (codigo_perfil,),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_perfil"])


def _exigir_usuario_ativo(dal, id_usuario: int) -> ServiceError | None:
    row = dal.read(
        "SELECT ativo FROM tb_usuario WHERE id_usuario = ?",
        (id_usuario,),
    )
    if row.empty:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")
    if int(row.iloc[0]["ativo"]) == 0:
        return ServiceError("Usuário inativo.", "usuario_inativo")
    return None


def _parse_id_opcional(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _validar_nome(nome: str) -> ServiceError | None:
    nome = (nome or "").strip()
    if not nome:
        return ServiceError("Nome é obrigatório.", "validacao")
    if len(nome) > NOME_MAX_LENGTH:
        return ServiceError(MSG_NOME_TAMANHO, "validacao")
    if not _NOME_ALFANUM.match(nome):
        return ServiceError(MSG_NOME_INVALIDO, "validacao")
    return None


def _erp_provider_nome(erp_service: Any) -> str:
    provider = getattr(erp_service, "provider", None)
    if isinstance(provider, str):
        return provider.strip().lower()
    return ""


def _permite_cadastro_manual_local(erp_service: Any) -> bool:
    raw = (os.getenv("ERP_ALLOW_MANUAL_USER_CREATE", "0") or "0").strip().lower()
    return _erp_provider_nome(erp_service) == "mock" and raw in ("1", "true", "yes", "on")


def _deve_validar_cadastro_corporativo(erp_service: Any) -> bool:
    if erp_service is None:
        return False
    provider = _erp_provider_nome(erp_service)
    if provider == "oracle":
        return True
    if provider == "mock":
        return not _permite_cadastro_manual_local(erp_service)
    return False


def _validar_vinculos_despachante(
    dal,
    id_empresa: Optional[int],
    id_turno: Optional[int],
    id_local: Optional[int],
) -> ServiceError | None:
    if not id_empresa or not id_turno or not id_local:
        return ServiceError(
            "Empresa, turno e local são obrigatórios para Despachante.",
            "validacao",
        )

    emp = dal.read(
        "SELECT id_empresa FROM tb_empresa WHERE id_empresa = ? AND ativo = 1",
        (id_empresa,),
    )
    if emp.empty:
        return ServiceError("Empresa inválida ou inativa.", "validacao")

    tur = dal.read(
        "SELECT id_turno FROM tb_turno WHERE id_turno = ? AND ativo = 1",
        (id_turno,),
    )
    if tur.empty:
        return ServiceError("Turno inválido ou inativo.", "validacao")

    loc = dal.read(
        "SELECT id_local FROM tb_local WHERE id_local = ? AND ativo = 1",
        (id_local,),
    )
    if loc.empty:
        return ServiceError("Local inválido ou inativo.", "validacao")

    return None


def _normalizar_vinculos(
    codigo_perfil: int,
    id_empresa: Any,
    id_turno: Any,
    id_local: Any,
) -> tuple[Optional[int], Optional[int], Optional[int]] | ServiceError:
    emp = _parse_id_opcional(id_empresa)
    tur = _parse_id_opcional(id_turno)
    loc = _parse_id_opcional(id_local)

    if codigo_perfil == PERFIL_DESPACHANTE:
        return emp, tur, loc
    return None, None, None


def listar_perfis(dal) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT id_perfil, codigo_perfil, descricao
        FROM tb_perfil
        ORDER BY codigo_perfil
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def listar_usuarios(dal) -> list[dict[str, Any]]:
    df = dal.read(
        f"""
        {_SELECT_USUARIO}
        ORDER BY u.matricula
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def _variantes_matricula(matricula: str) -> list[str]:
    """Gera variantes de matrícula para casar Oracle ↔ tb_usuario."""
    base = (matricula or "").strip()
    variantes: list[str] = []
    for cand in (base, base.lstrip("0") or "0"):
        if cand and cand not in variantes:
            variantes.append(cand)
        if cand.isdigit():
            z5 = str(int(cand)).zfill(5)
            if z5 not in variantes:
                variantes.append(z5)
            raw = str(int(cand))
            if raw not in variantes:
                variantes.append(raw)
    return variantes


def _buscar_usuario_local(dal, matricula: str, *, apenas_ativo: bool | None):
    """Busca usuário local por matrícula (com variantes de zeros à esquerda)."""
    for mat in _variantes_matricula(matricula):
        if apenas_ativo is True:
            sql = f"{_SELECT_USUARIO} WHERE u.matricula = ? AND u.ativo = 1"
        elif apenas_ativo is False:
            sql = f"{_SELECT_USUARIO} WHERE u.matricula = ? AND u.ativo = 0"
        else:
            sql = f"{_SELECT_USUARIO} WHERE u.matricula = ?"
        df = dal.read(sql, (mat,))
        if not df.empty:
            return df
    return None


def buscar_por_matricula(
    dal, matricula: str, erp_service=None
) -> dict[str, Any] | ServiceError:
    """
    Fluxo Pesquisar (cadastro de usuário):
    1) consulta Oracle/RH (obrigatória; mock só se ERP_PROVIDER=mock);
    2) se não achar no RH → 404;
    3) se já existir em tb_usuario → retorna usuário + ja_cadastrado;
    4) se só no RH → retorna dados para preencher novo cadastro.
    """
    matricula = (matricula or "").strip()
    if not matricula_valida(matricula):
        return ServiceError(MSG_MATRICULA_INVALIDA, "validacao")

    if erp_service is None:
        logger.error(
            "Busca por matrícula sem provider ERP | matricula=%s",
            matricula,
        )
        return ServiceError(
            "Não foi possível consultar o cadastro corporativo no momento. Tente novamente.",
            "erp_indisponivel",
        )

    provider = getattr(erp_service, "provider", "?")
    logger.info(
        "Busca matrícula | etapa=oracle_rh | ERP_PROVIDER=%s | matricula=%s",
        provider,
        matricula,
    )
    erp = consultar_funcionario_erp(erp_service, matricula)
    if isinstance(erp, ErpError):
        logger.info(
            "Busca matrícula | etapa=oracle_rh | resultado=%s | matricula=%s | "
            "proximo=nao_consulta_tb_usuario",
            erp.codigo,
            matricula,
        )
        if erp.codigo in (
            "funcionario_nao_encontrado",
            "nao_encontrado_erp",
            "nao_encontrado",
        ):
            return ServiceError(MSG_NAO_ENCONTRADA_RH, "nao_encontrado_rh")
        return ServiceError(erp.mensagem, erp.codigo)

    mat_erp = str(erp.get("matricula") or matricula).strip()
    nome_erp = str(erp.get("nome") or "").strip()
    foto_url = erp.get("foto_url")
    origem = str(erp.get("origem") or provider)
    logger.info(
        "Busca matrícula | etapa=oracle_rh | resultado=encontrado | "
        "ERP_PROVIDER=%s | origem_rh=%s | matricula=%s",
        provider,
        origem,
        mat_erp,
    )

    df_ativo = _buscar_usuario_local(dal, mat_erp, apenas_ativo=True)
    if df_ativo is not None and not df_ativo.empty:
        usuario = df_ativo.iloc[0].to_dict()
        anexar_foto_erp(erp_service, mat_erp, usuario)
        if foto_url and not usuario.get("foto_url"):
            usuario["foto_url"] = foto_url
        logger.info(
            "Busca matrícula | etapa=tb_usuario | resultado=encontrado_ativo | "
            "ja_cadastrado=true | id_usuario=%s | matricula=%s | "
            "nome_origem=tb_usuario | rh_origem=%s",
            usuario.get("id_usuario"),
            usuario.get("matricula"),
            origem,
        )
        return {
            "ja_cadastrado": True,
            "usuario": usuario,
            "mensagem": "Usuário já cadastrado.",
            "fonte_rh": origem,
        }

    df_inativo = _buscar_usuario_local(dal, mat_erp, apenas_ativo=False)
    if df_inativo is not None and not df_inativo.empty:
        logger.info(
            "Busca matrícula | etapa=tb_usuario | resultado=encontrado_inativo | "
            "matricula=%s",
            mat_erp,
        )
        return ServiceError("Usuário inativo.", "usuario_inativo")

    logger.info(
        "Busca matrícula | etapa=tb_usuario | resultado=nao_encontrado | "
        "ja_cadastrado=false | matricula=%s | prefill_origem=%s",
        mat_erp,
        origem,
    )
    return {
        "ja_cadastrado": False,
        "usuario": {
            "matricula": mat_erp,
            "nome": nome_erp,
            "foto_url": foto_url,
            "origem": origem,
            "ativo": True,
        },
        "mensagem": "Matrícula localizada no RH. Complete o cadastro e salve.",
        "fonte_rh": origem,
    }


def _esta_ativo(valor: Any) -> bool:
    """Normaliza BOOLEAN/int/numpy vindos do DAL."""
    if valor is None:
        return False
    if isinstance(valor, bool):
        return valor
    try:
        return int(valor) != 0
    except (TypeError, ValueError):
        return bool(valor)


def _carregar_usuario_por_matricula(dal, matricula: str) -> dict[str, Any]:
    row = dal.read(
        f"""
        {_SELECT_USUARIO}
        WHERE u.matricula = ?
        """,
        (matricula,),
    )
    return row.iloc[0].to_dict()


def criar_usuario(
    dal,
    matricula: str,
    nome: str,
    codigo_perfil: int,
    id_empresa: Any = None,
    id_turno: Any = None,
    id_local: Any = None,
    erp_service=None,
) -> dict[str, Any] | ServiceError:
    matricula = (matricula or "").strip()
    nome = (nome or "").strip()
    if not matricula:
        return ServiceError("Matrícula é obrigatória.", "validacao")
    if not matricula_valida(matricula):
        return ServiceError(MSG_MATRICULA_INVALIDA, "validacao")
    erro_nome = _validar_nome(nome)
    if erro_nome:
        return erro_nome
    if not codigo_perfil:
        return ServiceError("Perfil é obrigatório.", "validacao")

    if _deve_validar_cadastro_corporativo(erp_service):
        erp_ok = matricula_existe_erp(erp_service, matricula)
        if isinstance(erp_ok, ErpError):
            return ServiceError(erp_ok.mensagem, erp_ok.codigo)

    id_perfil = _perfil_id_por_codigo(dal, codigo_perfil)
    if id_perfil is None:
        return ServiceError("Perfil inválido.", "perfil_invalido")

    vinculos = _normalizar_vinculos(codigo_perfil, id_empresa, id_turno, id_local)
    if isinstance(vinculos, ServiceError):
        return vinculos
    emp_id, tur_id, loc_id = vinculos

    if codigo_perfil == PERFIL_DESPACHANTE:
        erro_v = _validar_vinculos_despachante(dal, emp_id, tur_id, loc_id)
        if erro_v:
            return erro_v

    existe = dal.read(
        "SELECT id_usuario, ativo FROM tb_usuario WHERE matricula = ?",
        (matricula,),
    )
    if not existe.empty:
        row_ex = existe.iloc[0]
        if _esta_ativo(row_ex["ativo"]):
            return ServiceError("Matrícula já cadastrada.", "matricula_duplicada")

        # Soft-deleted: reativa o mesmo id_usuario (sem INSERT / DELETE físico).
        id_usuario = int(row_ex["id_usuario"])
        senha_plana = gerar_senha_provisoria()
        senha_hash = hash_senha(senha_plana)
        ok = dal.update(
            """
            UPDATE tb_usuario
            SET nome = ?, senha = ?, id_perfil = ?,
                id_empresa = ?, id_turno = ?, id_local = ?,
                ativo = TRUE, trocar_senha = TRUE
            WHERE id_usuario = ?
            """,
            (nome, senha_hash, id_perfil, emp_id, tur_id, loc_id, id_usuario),
        )
        if not ok:
            return ServiceError("Falha ao reativar usuário.", "persistencia")

        usuario = _carregar_usuario_por_matricula(dal, matricula)
        usuario["senha_temporaria"] = senha_plana
        usuario["reativado"] = True
        if erp_service is not None:
            anexar_foto_erp(erp_service, matricula, usuario)
        return usuario

    senha_plana = gerar_senha_provisoria()
    senha_hash = hash_senha(senha_plana)
    ok = dal.create(
        """
        INSERT INTO tb_usuario (
            matricula, nome, senha, id_perfil,
            id_empresa, id_turno, id_local,
            ativo, trocar_senha
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, TRUE)
        """,
        (matricula, nome, senha_hash, id_perfil, emp_id, tur_id, loc_id),
    )
    if not ok:
        return ServiceError("Falha ao cadastrar usuário.", "persistencia")

    usuario = _carregar_usuario_por_matricula(dal, matricula)
    # Exposta uma única vez na resposta — nunca persistida em texto puro.
    usuario["senha_temporaria"] = senha_plana
    usuario["reativado"] = False
    if erp_service is not None:
        anexar_foto_erp(erp_service, matricula, usuario)
    return usuario


def atualizar_perfil(
    dal,
    id_usuario: int,
    codigo_perfil: int,
    nome: Optional[str] = None,
    id_empresa: Any = None,
    id_turno: Any = None,
    id_local: Any = None,
) -> dict[str, Any] | ServiceError:
    erro_ativo = _exigir_usuario_ativo(dal, id_usuario)
    if erro_ativo:
        return erro_ativo

    id_perfil = _perfil_id_por_codigo(dal, codigo_perfil)
    if id_perfil is None:
        return ServiceError("Perfil inválido.", "perfil_invalido")

    vinculos = _normalizar_vinculos(codigo_perfil, id_empresa, id_turno, id_local)
    if isinstance(vinculos, ServiceError):
        return vinculos
    emp_id, tur_id, loc_id = vinculos

    if codigo_perfil == PERFIL_DESPACHANTE:
        erro_v = _validar_vinculos_despachante(dal, emp_id, tur_id, loc_id)
        if erro_v:
            return erro_v

    nome_limpo = (nome or "").strip() if nome is not None else None
    if nome_limpo is not None:
        erro_nome = _validar_nome(nome_limpo)
        if erro_nome:
            return erro_nome
        ok = dal.update(
            """
            UPDATE tb_usuario
            SET id_perfil = ?, nome = ?,
                id_empresa = ?, id_turno = ?, id_local = ?
            WHERE id_usuario = ?
            """,
            (id_perfil, nome_limpo, emp_id, tur_id, loc_id, id_usuario),
        )
    else:
        ok = dal.update(
            """
            UPDATE tb_usuario
            SET id_perfil = ?,
                id_empresa = ?, id_turno = ?, id_local = ?
            WHERE id_usuario = ?
            """,
            (id_perfil, emp_id, tur_id, loc_id, id_usuario),
        )
    if not ok:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")

    row = dal.read(
        f"""
        {_SELECT_USUARIO}
        WHERE u.id_usuario = ?
        """,
        (id_usuario,),
    )
    if row.empty:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")
    return row.iloc[0].to_dict()


def excluir_usuario(dal, id_usuario: int) -> ServiceError | None:
    """Inativa usuário (RF-23 — soft delete: ativo = FALSE)."""
    row = dal.read(
        "SELECT id_usuario, ativo FROM tb_usuario WHERE id_usuario = ?",
        (id_usuario,),
    )
    if row.empty:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")
    if int(row.iloc[0]["ativo"]) == 0:
        return ServiceError("Usuário já está inativo.", "usuario_inativo")

    ok = dal.update(
        "UPDATE tb_usuario SET ativo = FALSE WHERE id_usuario = ?",
        (id_usuario,),
    )
    if not ok:
        return ServiceError("Falha ao inativar usuário.", "persistencia")
    return None


def resetar_senha(dal, id_usuario: int) -> dict[str, Any] | ServiceError:
    erro_ativo = _exigir_usuario_ativo(dal, id_usuario)
    if erro_ativo:
        return erro_ativo

    senha_plana = gerar_senha_provisoria()
    senha_hash = hash_senha(senha_plana)
    ok = dal.update(
        """
        UPDATE tb_usuario
        SET senha = ?, trocar_senha = TRUE
        WHERE id_usuario = ?
        """,
        (senha_hash, id_usuario),
    )
    if not ok:
        return ServiceError(
            "Não foi possível realizar o reset da senha!",
            "nao_encontrado",
        )

    row = dal.read(
        f"""
        {_SELECT_USUARIO}
        WHERE u.id_usuario = ?
        """,
        (id_usuario,),
    )
    if row.empty:
        return ServiceError(
            "Não foi possível realizar o reset da senha!",
            "nao_encontrado",
        )
    data = row.iloc[0].to_dict()
    data["senha_temporaria"] = senha_plana
    data["mensagem"] = "Reset de usuário realizado com sucesso!"
    return data
