import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal, database_name

dal = create_dal()
cur = ScriptDal(dal)
db = database_name(dal)

cur.execute(
    'SELECT COUNT(*) AS n FROM tb_item_map '
    'WHERE idmap IN (SELECT id_registro FROM tb_map WHERE id_usuario IN (1,2,3,4))'
)
print('Itens tb_item_map vinculados:', cur.fetchone()['n'])

cur.execute('''
    SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = ?
    AND REFERENCED_TABLE_NAME = 'tb_item_map'
''', (db,))
print('Tabelas que referenciam tb_item_map:')
for r in cur.fetchall():
    print(' ', r)

print()
print('Iniciando deleção em cascata...')

cur.execute('SELECT id_registro FROM tb_map WHERE id_usuario IN (1,2,3,4)')
map_ids = [r['id_registro'] for r in cur.fetchall()]
print('Mapas a deletar (id_registro):', map_ids)

if map_ids:
    placeholders = ','.join(['%s'] * len(map_ids))

    cur.execute(f'SELECT COUNT(*) AS n FROM tb_item_map WHERE idmap IN ({placeholders})', map_ids)
    n_items = int(cur.fetchone()['n'])
    print('Itens em tb_item_map:', n_items)

    if n_items > 0:
        cur.execute('''
            SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = ? AND REFERENCED_TABLE_NAME = 'tb_item_map'
        ''', (db,))
        child_tables = [(r['TABLE_NAME'], r['COLUMN_NAME']) for r in cur.fetchall()]
        print('Filhas de tb_item_map:', child_tables)

        cur.execute(f'SELECT id_item FROM tb_item_map WHERE idmap IN ({placeholders})', map_ids)
        item_ids = [r['id_item'] for r in cur.fetchall()]

        for tbl, col in child_tables:
            pl2 = ','.join(['%s'] * len(item_ids))
            cur.execute(f'DELETE FROM {tbl} WHERE {col} IN ({pl2})', item_ids)
            print(f'  Deletados de {tbl}')

        cur.execute(f'DELETE FROM tb_item_map WHERE idmap IN ({placeholders})', map_ids)
        print('Deletados de tb_item_map')

    cur.execute(f'DELETE FROM tb_map WHERE id_registro IN ({placeholders})', map_ids)
    print('Deletados de tb_map')

cur.execute('DELETE FROM tb_usuario WHERE matricula BETWEEN 10000 AND 10003')
print('Deletados de tb_usuario (matriculas 10000-10003)')

print()
print('Commit OK.')

df = dal.read('SELECT matricula, nome, ativo, trocar_senha FROM tb_usuario ORDER BY matricula')
print()
print('=== USUARIOS RESTANTES ===')
print(df.to_string(index=False))
