# -*- coding: utf-8 -*-
"""Recria os usuários administradores Proj_Map (59492 e 59817) com senha Admin_2026."""

from __future__ import annotations

import os
import sys

import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import create_dal

SENHA_PLAIN = "Admin_2026"
BCRYPT_ROUNDS = 12

ADMINS = (
    ("59492", "Marcos Antônio Correa Jordão"),
    ("59817", "Fabiano Souza De Freitas"),
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    senha_hash = bcrypt.hashpw(SENHA_PLAIN.encode("utf-8"), bcrypt.gensalt(BCRYPT_ROUNDS)).decode()
    dal = create_dal()

    try:
        perfil_df = dal.read(
            "SELECT id_perfil FROM tb_perfil WHERE codigo_perfil = 1 LIMIT 1"
        )
        if perfil_df.empty:
            print("Erro: perfil Administrador (codigo_perfil=1) não encontrado.")
            return 1
        id_perfil = int(perfil_df.iloc[0]["id_perfil"])

        existentes_df = dal.read(
            """
            SELECT id_usuario, matricula
            FROM tb_usuario
            WHERE matricula IN ('59492', '59817')
            """
        )
        existentes = {
            str(row["matricula"]): int(row["id_usuario"])
            for _, row in existentes_df.iterrows()
        }

        for matricula in ("59492", "59817"):
            id_usuario = existentes.get(matricula)
            if id_usuario is not None:
                dal.delete(
                    "DELETE FROM tb_avaria WHERE id_usuario = ?",
                    (id_usuario,),
                )
                dal.delete(
                    "DELETE FROM tb_usuario WHERE id_usuario = ?",
                    (id_usuario,),
                )
                print(f"Usuário {matricula} (id={id_usuario}) removido.")

        for matricula, nome in ADMINS:
            dal.create(
                """
                INSERT INTO tb_usuario (
                    matricula, nome, senha, id_perfil,
                    id_empresa, id_turno, id_local,
                    ativo, trocar_senha
                ) VALUES (?, ?, ?, ?, NULL, NULL, NULL, 1, 0)
                """,
                (matricula, nome, senha_hash, id_perfil),
            )
            print(f"Usuário {matricula} criado: {nome}")

        verif_df = dal.read(
            """
            SELECT u.matricula, u.nome, u.id_empresa, u.id_turno, u.id_local,
                   u.ativo, u.trocar_senha, p.descricao AS perfil
            FROM tb_usuario u
            INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
            WHERE u.matricula IN ('59492', '59817')
            ORDER BY u.matricula
            """
        )
        print("\nVerificação:")
        for _, row in verif_df.iterrows():
            print(
                f"  matricula={row['matricula']} nome={row['nome']} perfil={row['perfil']}"
            )
            print(
                f"    empresa={row['id_empresa']} turno={row['id_turno']} "
                f"local={row['id_local']} ativo={row['ativo']} "
                f"trocar_senha={row['trocar_senha']}"
            )

        ok = bcrypt.checkpw(SENHA_PLAIN.encode("utf-8"), senha_hash.encode("utf-8"))
        print(f"\nSenha '{SENHA_PLAIN}' verificada no hash: {ok}")
        return 0
    except Exception as exc:
        print(f"Erro: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
