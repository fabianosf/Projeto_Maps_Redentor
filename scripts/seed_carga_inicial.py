# -*- coding: utf-8 -*-
"""
Limpeza total do banco map + carga inicial reproduzível.

Uso (na raiz do projeto):
  python -u scripts/seed_carga_inicial.py

Regras:
  - TRUNCATE de todas as tabelas (FOREIGN_KEY_CHECKS=0)
  - Senha dos usuários: 12345 (bcrypt cost 12)
  - Perfis: 1=Administrador, 2=Despachante, 3=Inspetor
  - Empresas: 1=Futuro, 2=Redentor, 3=Barra (compatível com a UI)
"""

from __future__ import annotations

import os
import random
import string
import sys

import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal, list_tables

SENHA_PLANA = "12345"
BCRYPT_ROUNDS = 12

PERFIS = [
    (1, "Administrador"),
    (2, "Despachante"),
    (3, "Inspetor"),
]

TURNOS = [
    (1, "TURNO 01"),
    (2, "TURNO 02"),
    (3, "TURNO 03"),
]

EMPRESAS = [
    (1, "Futuro"),
    (2, "Redentor"),
    (3, "Barra"),
]

USUARIOS = [
    ("10000", "João Alves Brito", 1),
    ("10001", "Maria Lucia Azevedo", 2),
    ("10002", "José Carlos Neves", 3),
]

LOCAIS = [
    (10, "Cidade De Deus"),
    (20, "Gávea"),
    (30, "Tanque"),
]

LINHAS = [
    (550, "Cidade De Deus - Gávea", 1, 10, 20),
    (565, "Tanque - Gávea", 2, 20, 30),
]

FROTAS = (
    [f"30{101 + i}" for i in range(5)]
    + [f"47{101 + i}" for i in range(5)]
    + [f"13{101 + i}" for i in range(5)]
)


def log(msg: str) -> None:
    print(msg, flush=True)


def hash_senha(senha_plana: str) -> str:
    hashed = bcrypt.hashpw(
        senha_plana.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    )
    return hashed.decode("utf-8")


def count(cur: ScriptDal, tabela: str) -> int:
    cur.execute(f"SELECT COUNT(*) AS qtd FROM `{tabela}`")
    row = cur.fetchone()
    return int(row["qtd"]) if row else 0


def placa_aleatoria(rng: random.Random, usadas: set[str]) -> str:
    letras = string.ascii_uppercase
    while True:
        if rng.random() < 0.5:
            placa = (
                "".join(rng.choice(letras) for _ in range(3))
                + "-"
                + "".join(rng.choice(string.digits) for _ in range(4))
            )
        else:
            placa = (
                "".join(rng.choice(letras) for _ in range(3))
                + rng.choice(string.digits)
                + rng.choice(letras)
                + "".join(rng.choice(string.digits) for _ in range(2))
            )
        if placa not in usadas:
            usadas.add(placa)
            return placa


def id_por_codigo(cur: ScriptDal, tabela: str, pk: str, codigo_col: str, codigo: int) -> int:
    cur.execute(
        f"SELECT `{pk}` AS id FROM `{tabela}` WHERE `{codigo_col}` = %s",
        (codigo,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"{tabela}: código {codigo} não encontrado")
    return int(row["id"])


def limpar_tudo(cur: ScriptDal, tabelas: list[str]) -> None:
    log("=== LIMPEZA ===")
    cur.execute("SET SESSION innodb_lock_wait_timeout = 10")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for tabela in tabelas:
        try:
            cur.execute(f"DELETE FROM `{tabela}`")
            cur.execute(f"ALTER TABLE `{tabela}` AUTO_INCREMENT = 1")
            log(f"  CLEAR {tabela} [OK]")
        except Exception as exc:
            log(f"  CLEAR {tabela} FALHA: {exc}")
            raise
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")


def carregar(cur: ScriptDal) -> dict[str, int]:
    log("=== CARGA ===")
    inseridos: dict[str, int] = {}

    for codigo, descricao in PERFIS:
        cur.execute(
            "INSERT INTO tb_perfil (codigo_perfil, descricao) VALUES (%s, %s)",
            (codigo, descricao),
        )
    inseridos["tb_perfil"] = len(PERFIS)
    log(f"  tb_perfil: {inseridos['tb_perfil']}")

    for codigo, descricao in TURNOS:
        cur.execute(
            "INSERT INTO tb_turno (codigo_turno, descricao, ativo) VALUES (%s, %s, 1)",
            (codigo, descricao),
        )
    inseridos["tb_turno"] = len(TURNOS)
    log(f"  tb_turno: {inseridos['tb_turno']}")

    for codigo, descricao in EMPRESAS:
        cur.execute(
            "INSERT INTO tb_empresa (codigo_empresa, descricao, ativo) VALUES (%s, %s, 1)",
            (codigo, descricao),
        )
    inseridos["tb_empresa"] = len(EMPRESAS)
    log(f"  tb_empresa: {inseridos['tb_empresa']}")

    senha_hash = hash_senha(SENHA_PLANA)
    log(f"  hash bcrypt gerado (prefixo {senha_hash[:7]}...)")
    for matricula, nome, codigo_perfil in USUARIOS:
        id_perfil = id_por_codigo(cur, "tb_perfil", "id_perfil", "codigo_perfil", codigo_perfil)
        cur.execute(
            """
            INSERT INTO tb_usuario
                (matricula, nome, senha, id_perfil, ativo, trocar_senha)
            VALUES (%s, %s, %s, %s, 1, 0)
            """,
            (matricula, nome, senha_hash, id_perfil),
        )
    inseridos["tb_usuario"] = len(USUARIOS)
    log(f"  tb_usuario: {inseridos['tb_usuario']} (senha={SENHA_PLANA})")

    for codigo, descricao in LOCAIS:
        cur.execute(
            "INSERT INTO tb_local (codigo_local, descricao, ativo) VALUES (%s, %s, 1)",
            (codigo, descricao),
        )
    inseridos["tb_local"] = len(LOCAIS)
    log(f"  tb_local: {inseridos['tb_local']}")

    for codigo_linha, descricao, cod_emp, cod_ori, cod_dst in LINHAS:
        id_empresa = id_por_codigo(cur, "tb_empresa", "id_empresa", "codigo_empresa", cod_emp)
        id_origem = id_por_codigo(cur, "tb_local", "id_local", "codigo_local", cod_ori)
        id_destino = id_por_codigo(cur, "tb_local", "id_local", "codigo_local", cod_dst)
        cur.execute(
            """
            INSERT INTO tb_linha (
                codigo_linha, id_empresa, descricao,
                id_local_origem, id_local_destino, ativo
            ) VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (codigo_linha, id_empresa, descricao, id_origem, id_destino),
        )
    inseridos["tb_linha"] = len(LINHAS)
    log(f"  tb_linha: {inseridos['tb_linha']}")

    rng = random.Random(20260804)
    placas: set[str] = set()
    for frota in FROTAS:
        codigo_veiculo = int(frota)
        placa = placa_aleatoria(rng, placas)
        cur.execute(
            """
            INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa, ativo)
            VALUES (%s, %s, %s, 1)
            """,
            (codigo_veiculo, frota, placa),
        )
        log(f"    veiculo {frota} placa={placa}")
    inseridos["tb_veiculo"] = len(FROTAS)
    log(f"  tb_veiculo: {inseridos['tb_veiculo']}")

    indicadores = [
        (1, "QTD(M)/ P", "Quantidade média de passageiros"),
        (2, "OCUP", "Taxa de ocupação do veículo"),
        (3, "ATR/M", "Atraso médio no ponto"),
        (4, "INT/V", "Intervalo médio entre viagens"),
        (5, "KMT/D", "Quilometragem diária percorrida"),
    ]
    for cod_ind, sigla, detalhe in indicadores:
        cur.execute(
            """
            INSERT INTO tb_indicador (cod_ind, descricao, detalhe)
            VALUES (%s, %s, %s)
            """,
            (cod_ind, sigla, detalhe),
        )
    inseridos["tb_indicador"] = len(indicadores)
    log(f"  tb_indicador: {inseridos['tb_indicador']}")

    id_perfil_insp = id_por_codigo(cur, "tb_perfil", "id_perfil", "codigo_perfil", 3)
    cur.execute(
        """
        INSERT INTO tb_ind_perf (id_ind, id_perfil)
        SELECT id_ind, %s FROM tb_indicador WHERE cod_ind IN (1, 2)
        """,
        (id_perfil_insp,),
    )
    inseridos["tb_ind_perf"] = 2
    log(f"  tb_ind_perf: {inseridos['tb_ind_perf']} (Inspetor: QTD + OCUP)")

    return inseridos


def validar(cur: ScriptDal, tabelas: list[str], esperados: dict[str, int]) -> bool:
    log("=== VALIDAÇÃO (contagem) ===")
    ok_geral = True
    for tabela in tabelas:
        qtd = count(cur, tabela)
        exp = esperados.get(tabela, 0)
        marca = "OK" if qtd == exp else "DIVERGENTE"
        if qtd != exp:
            ok_geral = False
        log(f"  {tabela}: {qtd} (esperado {exp}) [{marca}]")

    log("\n=== AMOSTRA ===")
    cur.execute("SELECT codigo_perfil, descricao FROM tb_perfil ORDER BY codigo_perfil")
    log(f"tb_perfil: {cur.fetchall()}")
    cur.execute("SELECT codigo_turno, descricao, ativo FROM tb_turno ORDER BY codigo_turno")
    log(f"tb_turno: {cur.fetchall()}")
    cur.execute("SELECT codigo_empresa, descricao, ativo FROM tb_empresa ORDER BY codigo_empresa")
    log(f"tb_empresa: {cur.fetchall()}")
    cur.execute(
        """
        SELECT u.matricula, u.nome, p.descricao AS perfil, u.ativo, u.trocar_senha,
               LEFT(u.senha, 7) AS senha_prefix
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        ORDER BY u.matricula
        """
    )
    log(f"tb_usuario: {cur.fetchall()}")
    cur.execute("SELECT codigo_local, descricao, ativo FROM tb_local ORDER BY codigo_local")
    log(f"tb_local: {cur.fetchall()}")
    cur.execute(
        """
        SELECT l.codigo_linha, l.descricao, e.descricao AS empresa,
               o.codigo_local AS origem, d.codigo_local AS destino, l.ativo
        FROM tb_linha l
        INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        INNER JOIN tb_local o ON o.id_local = l.id_local_origem
        INNER JOIN tb_local d ON d.id_local = l.id_local_destino
        ORDER BY l.codigo_linha
        """
    )
    log(f"tb_linha: {cur.fetchall()}")
    cur.execute(
        """
        SELECT codigo_veiculo, numero_frota, placa, ativo
        FROM tb_veiculo
        ORDER BY numero_frota
        """
    )
    log(f"tb_veiculo: {cur.fetchall()}")
    return ok_geral


def main() -> int:
    dal = create_dal()
    log(f"Conectando via DAL ({dal.connection_string}) ...")
    if not dal.test_connection():
        log("Falha na conexão.")
        return 1

    cur = ScriptDal(dal)
    tabelas = list_tables(dal)
    if not tabelas:
        log("Nenhuma tabela encontrada.")
        return 1
    log("Tabelas: " + ", ".join(tabelas))

    limpar_tudo(cur, tabelas)
    inseridos = carregar(cur)

    esperados = {t: 0 for t in tabelas}
    esperados.update(inseridos)
    if not validar(cur, tabelas, esperados):
        log("\nVALIDAÇÃO FALHOU.")
        return 1

    log("\nCarga inicial concluída com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
