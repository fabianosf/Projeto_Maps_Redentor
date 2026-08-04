# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Cadastro de usuários — RF-RN-013, RF-RN-014, RF-RN-015."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from .auth_service import hash_senha
from .constants import SENHA_PROVISORIA

_NOME_ALFANUM = re.compile(r"^[A-Za-zÀ-ÿ0-9\s]+$")


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
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               p.id_perfil, p.codigo_perfil, p.descricao AS perfil_descricao
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        ORDER BY u.matricula
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def buscar_por_matricula(dal, matricula: str) -> dict[str, Any] | ServiceError:
    matricula = (matricula or "").strip()
    if not matricula or not matricula.isdigit():
        return ServiceError("Informe uma matrícula numérica válida.", "validacao")

    df = dal.read(
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               p.id_perfil, p.codigo_perfil, p.descricao AS perfil_descricao
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.matricula = ?
        """,
        (matricula,),
    )
    if df.empty:
        return ServiceError("Matrícula não encontrada", "nao_encontrado")
    return df.iloc[0].to_dict()


def criar_usuario(
    dal,
    matricula: str,
    nome: str,
    codigo_perfil: int,
) -> dict[str, Any] | ServiceError:
    matricula = (matricula or "").strip()
    nome = (nome or "").strip()
    if not matricula or not nome:
        return ServiceError("Matrícula e nome são obrigatórios.", "validacao")
    if not matricula.isdigit():
        return ServiceError("Matrícula deve ser exclusivamente numérica.", "validacao")
    if not _NOME_ALFANUM.match(nome):
        return ServiceError(
            "Nome deve ser alfanumérico (letras, números e espaços).",
            "validacao",
        )
    if not codigo_perfil:
        return ServiceError("Perfil é obrigatório.", "validacao")

    id_perfil = _perfil_id_por_codigo(dal, codigo_perfil)
    if id_perfil is None:
        return ServiceError("Perfil inválido.", "perfil_invalido")

    existe = dal.read(
        "SELECT id_usuario FROM tb_usuario WHERE matricula = ?",
        (matricula,),
    )
    if not existe.empty:
        return ServiceError("Matrícula já cadastrada.", "matricula_duplicada")

    # Senha padrão "12345" → hash bcrypt; trocar_senha=1; ativo=1
    senha_hash = hash_senha(SENHA_PROVISORIA)
    ok = dal.create(
        """
        INSERT INTO tb_usuario (matricula, nome, senha, id_perfil, ativo, trocar_senha)
        VALUES (?, ?, ?, ?, 1, 1)
        """,
        (matricula, nome, senha_hash, id_perfil),
    )
    if not ok:
        return ServiceError("Falha ao cadastrar usuário.", "persistencia")

    row = dal.read(
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               p.codigo_perfil, p.descricao AS perfil_descricao
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.matricula = ?
        """,
        (matricula,),
    )
    return row.iloc[0].to_dict()


def atualizar_perfil(
    dal, id_usuario: int, codigo_perfil: int, nome: Optional[str] = None
) -> dict[str, Any] | ServiceError:
    id_perfil = _perfil_id_por_codigo(dal, codigo_perfil)
    if id_perfil is None:
        return ServiceError("Perfil inválido.", "perfil_invalido")

    nome_limpo = (nome or "").strip() if nome is not None else None
    if nome_limpo is not None:
        if not nome_limpo:
            return ServiceError("Nome é obrigatório.", "validacao")
        if not _NOME_ALFANUM.match(nome_limpo):
            return ServiceError(
                "Nome deve ser alfanumérico (letras, números e espaços).",
                "validacao",
            )
        ok = dal.update(
            "UPDATE tb_usuario SET id_perfil = ?, nome = ? WHERE id_usuario = ?",
            (id_perfil, nome_limpo, id_usuario),
        )
    else:
        ok = dal.update(
            "UPDATE tb_usuario SET id_perfil = ? WHERE id_usuario = ?",
            (id_perfil, id_usuario),
        )
    if not ok:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")

    row = dal.read(
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               p.codigo_perfil, p.descricao AS perfil_descricao
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.id_usuario = ?
        """,
        (id_usuario,),
    )
    if row.empty:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")
    return row.iloc[0].to_dict()


def excluir_usuario(dal, id_usuario: int) -> ServiceError | None:
    em_uso = dal.read(
        "SELECT id_registro FROM tb_map WHERE id_usuario = ? LIMIT 1",
        (id_usuario,),
    )
    if not em_uso.empty:
        return ServiceError(
            "Usuário vinculado a MAPA(s); não é possível excluir.",
            "usuario_em_uso",
        )

    ok = dal.delete("DELETE FROM tb_usuario WHERE id_usuario = ?", (id_usuario,))
    if not ok:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")
    return None


def resetar_senha(dal, id_usuario: int) -> dict[str, Any] | ServiceError:
    senha_hash = hash_senha(SENHA_PROVISORIA)
    ok = dal.update(
        """
        UPDATE tb_usuario
        SET senha = ?, trocar_senha = 1
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
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               p.codigo_perfil, p.descricao AS perfil_descricao
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
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
    data["mensagem"] = "Reset de usuário realizado com sucesso!"
    return data
