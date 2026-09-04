"""
Seed: 12 motoristas (4 por empresa), 2 linhas por empresa.
Cria locais e linhas ausentes antes de inserir os motoristas.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import create_dal

dal = create_dal()

# ─── 1. Novos locais (para linhas da Barra) ──────────────────────────────────
novos_locais = [
    (40, 'Recreio dos Bandeirantes'),
    (50, 'Barra da Tijuca'),
]

for cod, desc in novos_locais:
    existe = dal.read('SELECT id_local FROM tb_local WHERE codigo_local = ?', (cod,))
    if existe.empty:
        dal.create(
            'INSERT INTO tb_local (codigo_local, descricao) VALUES (?, ?)',
            (cod, desc),
        )
        print(f'  [LOCAL] Criado: {cod} - {desc}')
    else:
        print(f'  [LOCAL] Já existe: {cod} - {desc}')

# ─── 2. Carregar IDs dos locais ───────────────────────────────────────────────
def local_id(codigo: int) -> int:
    df = dal.read('SELECT id_local FROM tb_local WHERE codigo_local = ?', (codigo,))
    return int(df.iloc[0]['id_local'])

id_cidade_de_deus     = local_id(10)   # Cidade De Deus
id_gavea              = local_id(20)   # Gávea
id_tanque             = local_id(30)   # Tanque
id_recreio            = local_id(40)   # Recreio dos Bandeirantes
id_barra_da_tijuca    = local_id(50)   # Barra da Tijuca

# ─── 3. Carregar IDs das empresas ────────────────────────────────────────────
def empresa_id(codigo: int) -> int:
    df = dal.read('SELECT id_empresa FROM tb_empresa WHERE codigo_empresa = ?', (codigo,))
    return int(df.iloc[0]['id_empresa'])

id_futuro   = empresa_id(1)
id_redentor = empresa_id(2)
id_barra    = empresa_id(3)

# ─── 4. Novas linhas (2 por empresa) ─────────────────────────────────────────
novas_linhas = [
    (555, id_futuro,   'Cidade De Deus - Tanque',          id_cidade_de_deus,  id_tanque),
    (575, id_redentor, 'Gávea - Tanque',                   id_gavea,           id_tanque),
    (580, id_barra,    'Recreio - Gávea',                  id_recreio,         id_gavea),
    (590, id_barra,    'Barra da Tijuca - Cidade De Deus', id_barra_da_tijuca, id_cidade_de_deus),
]

for cod, id_emp, desc, id_orig, id_dest in novas_linhas:
    existe = dal.read('SELECT id_linha FROM tb_linha WHERE codigo_linha = ?', (cod,))
    if existe.empty:
        dal.create(
            '''INSERT INTO tb_linha
               (codigo_linha, id_empresa, descricao, id_local_origem, id_local_destino)
               VALUES (?, ?, ?, ?, ?)''',
            (cod, id_emp, desc, id_orig, id_dest),
        )
        print(f'  [LINHA] Criada: {cod} - {desc}')
    else:
        print(f'  [LINHA] Já existe: {cod} - {desc}')

# ─── 5. 12 motoristas (4 por empresa) ────────────────────────────────────────
motoristas = [
    ('71001', 'Carlos Eduardo Santos'),
    ('71002', 'José Ribeiro Neto'),
    ('71003', 'Antônio Ferreira Lima'),
    ('71004', 'Francisco Alves Costa'),
    ('72001', 'Roberto Silva Pereira'),
    ('72002', 'Marcos Oliveira Souza'),
    ('72003', 'Paulo Mendes Rocha'),
    ('72004', 'Lucas Rodrigues Melo'),
    ('73001', 'João Carlos Barros'),
    ('73002', 'Pedro Augusto Faria'),
    ('73003', 'André Luiz Campos'),
    ('73004', 'Felipe Nascimento Cruz'),
]

print()
inseridos = 0
for mat, nome in motoristas:
    existe = dal.read('SELECT matricula FROM tb_motorista WHERE matricula = ?', (mat,))
    if existe.empty:
        dal.create(
            'INSERT INTO tb_motorista (matricula, nome) VALUES (?, ?)',
            (mat, nome),
        )
        print(f'  [MOTORISTA] Inserido: {mat} - {nome}')
        inseridos += 1
    else:
        print(f'  [MOTORISTA] Já existe: {mat} - {nome}')

print()
print(f'Concluído. {inseridos} motoristas inseridos.')

print()
print('=== RESUMO POR EMPRESA ===')
df = dal.read('''
    SELECT e.descricao as empresa,
           l.codigo_linha,
           l.descricao as linha,
           lo.descricao as origem,
           ld.descricao as destino
    FROM tb_linha l
    JOIN tb_empresa e ON e.id_empresa = l.id_empresa
    JOIN tb_local lo   ON lo.id_local  = l.id_local_origem
    JOIN tb_local ld   ON ld.id_local  = l.id_local_destino
    ORDER BY e.codigo_empresa, l.codigo_linha
''')
print(df.to_string(index=False))

print()
print('=== MOTORISTAS CADASTRADOS ===')
df2 = dal.read('SELECT matricula, nome FROM tb_motorista ORDER BY matricula')
print(df2.to_string(index=False))
