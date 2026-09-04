"""Debug: testa o que o DAL retorna para o usuario 60005"""
import sys, os
ROOT = r'E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP'
sys.path.insert(0, os.path.join(ROOT, 'BackEnd'))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from DAL.DAL import DAL
dal = DAL('map')

df = dal.read(
    """SELECT u.id_usuario, u.matricula, u.nome, u.senha, u.ativo, u.trocar_senha,
              p.codigo_perfil
       FROM tb_usuario u
       INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
       WHERE u.matricula = ?""",
    ('60005',)
)
print("DataFrame completo:")
print(df.to_string())
print()
row = df.iloc[0]
print("trocar_senha raw:", repr(row["trocar_senha"]))
print("bool(int(...))  :", bool(int(row["trocar_senha"])))
