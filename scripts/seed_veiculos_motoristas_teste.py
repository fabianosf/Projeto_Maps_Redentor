"""Verifica carro 30128 e, se ausente, cadastra veículos/motoristas de teste."""

from __future__ import annotations

import pymysql

# numero_frota 30128 + outros; codigo_veiculo = número da frota
VEICULOS = [
    (30128, "30128", "RST1A28"),
    (30129, "30129", "RST1B29"),
    (30130, "30130", "RST1C30"),
    (30201, "30201", "UVW2D01"),
    (30202, "30202", "UVW2E02"),
]

MOTORISTAS = [
    ("1000", "Motorista Teste 1000"),
    ("2001", "Motorista Teste 2001"),
    ("2002", "Motorista Teste 2002"),
    ("2003", "Motorista Teste 2003"),
    ("3001", "Motorista Teste 3001"),
]


def main() -> None:
    conn = pymysql.connect(
        host="10.1.1.29",
        port=3306,
        user="alberto",
        password="at5001",
        database="map",
        connect_timeout=8,
        autocommit=True,
        charset="utf8mb4",
    )
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo
        FROM tb_veiculo
        WHERE numero_frota = %s OR codigo_veiculo = %s
        """,
        ("30128", 30128),
    )
    existente = cur.fetchall()
    print("VERIFICACAO_30128:", existente)

    veiculos_inseridos = []
    reativado_30128 = False

    if existente:
        print("STATUS: carro 30128 JA existia.")
        # API lista apenas ativo=1; reativa se estiver inativo (necessario para teste)
        ativo = int(existente[0][4] or 0)
        if ativo != 1:
            cur.execute(
                "UPDATE tb_veiculo SET ativo=1 WHERE numero_frota=%s",
                ("30128",),
            )
            reativado_30128 = True
            print("REATIVADO_30128: ativo 0 -> 1")
        # Completa frota de teste sem sobrescrever o 30128
        for codigo, frota, placa in VEICULOS:
            if frota == "30128":
                continue
            cur.execute(
                "SELECT id_veiculo FROM tb_veiculo WHERE numero_frota=%s OR codigo_veiculo=%s OR placa=%s",
                (frota, codigo, placa),
            )
            if cur.fetchone():
                print(f"SKIP_VEICULO: {frota} (ja existe)")
                continue
            cur.execute(
                """
                INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa, ativo)
                VALUES (%s, %s, %s, 1)
                """,
                (codigo, frota, placa),
            )
            veiculos_inseridos.append((codigo, frota, placa))
            print(f"INSERT_VEICULO: {frota} / {placa}")
    else:
        print("STATUS: carro 30128 AUSENTE — cadastrando veiculos de teste.")
        for codigo, frota, placa in VEICULOS:
            cur.execute(
                "SELECT id_veiculo FROM tb_veiculo WHERE numero_frota=%s OR codigo_veiculo=%s OR placa=%s",
                (frota, codigo, placa),
            )
            if cur.fetchone():
                print(f"SKIP_VEICULO: {frota} (ja existe)")
                continue
            cur.execute(
                """
                INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa, ativo)
                VALUES (%s, %s, %s, 1)
                """,
                (codigo, frota, placa),
            )
            veiculos_inseridos.append((codigo, frota, placa))
            print(f"INSERT_VEICULO: {frota} / {placa}")

    # Garante matrículas de teste (sem alterar existentes)
    motoristas_inseridos = []
    for matricula, nome in MOTORISTAS:
        cur.execute("SELECT id_motorista FROM tb_motorista WHERE matricula=%s", (matricula,))
        if cur.fetchone():
            print(f"SKIP_MOTORISTA: {matricula} (ja existe)")
            continue
        cur.execute(
            """
            INSERT INTO tb_motorista (matricula, nome, ativo)
            VALUES (%s, %s, 1)
            """,
            (matricula, nome),
        )
        motoristas_inseridos.append((matricula, nome))
        print(f"INSERT_MOTORISTA: {matricula} / {nome}")

    cur.execute(
        """
        SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo
        FROM tb_veiculo
        WHERE numero_frota = %s OR codigo_veiculo = %s
        """,
        ("30128", 30128),
    )
    print("VERIFICACAO_30128_FINAL:", cur.fetchall())
    print("REATIVADO_30128:", reativado_30128)
    print("VEICULOS_INSERIDOS:", veiculos_inseridos)
    print("MOTORISTAS_INSERIDOS:", motoristas_inseridos)
    cur.execute(
        "SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo FROM tb_veiculo WHERE ativo=1 ORDER BY numero_frota"
    )
    print("VEICULOS_ATIVOS:", cur.fetchall())
    cur.execute(
        "SELECT id_motorista, matricula, nome, ativo FROM tb_motorista WHERE ativo=1 ORDER BY matricula"
    )
    print("MOTORISTAS_ATIVOS:", cur.fetchall())
    conn.close()


if __name__ == "__main__":
    main()
