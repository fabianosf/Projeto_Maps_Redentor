"""
Popular banco com dados realistas para captura de telas.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt

from dal_util import ScriptDal, create_dal

dal = create_dal()
cur = ScriptDal(dal)

# ── 1. Usuário de captura: 60001 sem trocar_senha ──────────────────────────────
novo_hash = bcrypt.hashpw('Senha@2025'.encode(), bcrypt.gensalt(12)).decode()
cur.execute('UPDATE tb_usuario SET senha=%s, trocar_senha=0 WHERE matricula=60001', (novo_hash,))
print('Usuário 60001 configurado (trocar_senha=0, nova senha: Senha@2025)')

# ── 2. Verificar turnos ────────────────────────────────────────────────────────
cur.execute('SELECT id_turno, descricao FROM tb_turno')
turnos = cur.fetchall()
print('Turnos:', turnos)

if not turnos:
    cur.execute("INSERT INTO tb_turno (descricao) VALUES ('Manhã'), ('Tarde'), ('Noite')")
    cur.execute('SELECT id_turno, descricao FROM tb_turno')
    turnos = cur.fetchall()
    print('Turnos criados:', turnos)

id_turno = turnos[0]['id_turno']

# ── 3. Obter IDs necessários ───────────────────────────────────────────────────
cur.execute('SELECT id_usuario FROM tb_usuario WHERE matricula=60001')
id_usuario = cur.fetchone()['id_usuario']

cur.execute('SELECT id_linha, codigo_linha, descricao FROM tb_linha ORDER BY codigo_linha')
linhas = cur.fetchall()
print('Linhas:', linhas)
id_linha = linhas[0]['id_linha']

# ── 4. Verificar veículos ──────────────────────────────────────────────────────
cur.execute('DESCRIBE tb_veiculo')
cols_v = [r['Field'] for r in cur.fetchall()]
print('Colunas tb_veiculo:', cols_v)

cur.execute('SELECT * FROM tb_veiculo LIMIT 5')
veiculos = cur.fetchall()
print('Veículos:', veiculos)

if not veiculos:
    cur.execute('SELECT COUNT(*) AS n FROM tb_veiculo')
    if int(cur.fetchone()['n']) == 0:
        for placa in ['RIO-1A23', 'RIO-2B34', 'RIO-3C45', 'RIO-4D56']:
            cur.execute('INSERT INTO tb_veiculo (placa) VALUES (%s)', (placa,))
        cur.execute('SELECT * FROM tb_veiculo LIMIT 5')
        veiculos = cur.fetchall()
        print('Veículos criados:', veiculos)

cur.execute('SELECT id_veiculo FROM tb_veiculo LIMIT 1')
id_veiculo = cur.fetchone()['id_veiculo']

# ── 5. Obter motoristas ────────────────────────────────────────────────────────
cur.execute('SELECT id_motorista, matricula, nome FROM tb_motorista ORDER BY matricula LIMIT 4')
motoristas = cur.fetchall()
print('Motoristas:', motoristas)

# ── 6. Criar 2 MAPs com registros ────────────────────────────────────────────
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

for i, (data, cod_map) in enumerate([(today, 101), (yesterday, 100)]):
    cur.execute('SELECT id_registro FROM tb_map WHERE cod_map=%s', (cod_map,))
    if cur.fetchone():
        print(f'MAP {cod_map} já existe')
        continue

    cur.execute('''
        INSERT INTO tb_map (cod_map, id_usuario, id_linha, id_turno, data,
                            inicio_jornada_des, fim_jornada_des, observacao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        cod_map, id_usuario, id_linha, id_turno, data,
        datetime.datetime.combine(data, datetime.time(5, 0)),
        datetime.datetime.combine(data, datetime.time(13, 0)) if i == 1 else None,
        None
    ))
    id_map = cur.lastrowid
    print(f'MAP {cod_map} criado: id={id_map}')

    if motoristas:
        for j, mot in enumerate(motoristas[:3]):
            id_mot = mot['id_motorista']
            cur.execute('''
                INSERT INTO tb_item_map (idmap, id_veiculo, id_motorista,
                                        hor_ini_jor, hor_fim_jor, chegada_ponto)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                id_map, id_veiculo, id_mot,
                datetime.datetime.combine(data, datetime.time(5 + j, 0)),
                datetime.datetime.combine(data, datetime.time(13 + j, 0)) if i == 1 else None,
                datetime.datetime.combine(data, datetime.time(5 + j, 15)) if i == 1 else None,
            ))
        print(f'  {min(3, len(motoristas))} itens criados')

print()
print('Banco populado com sucesso.')
