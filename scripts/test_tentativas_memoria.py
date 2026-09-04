import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from dal_util import column_exists, create_dal

from BackEnd.app import get_dal
from BackEnd.auth_service import AuthError, autenticar_login
from BackEnd.login_attempt_store import obter_tentativas, resetar_tentativas

dal = create_dal()
if column_exists(dal, "tb_usuario", "tentativas_login"):
    dal.update("ALTER TABLE tb_usuario DROP COLUMN tentativas_login")
    print("Coluna tentativas_login removida.")
else:
    print("Coluna tentativas_login ja ausente.")

app_dal = get_dal()
MAT = "60001"
app_dal.update("UPDATE tb_usuario SET ativo=1 WHERE matricula=%s", (MAT,))
resetar_tentativas(MAT)

for i in range(1, 4):
    r = autenticar_login(app_dal, MAT, "errada")
    msg = r.mensagem if isinstance(r, AuthError) else "OK"
    ativo = app_dal.read("SELECT ativo FROM tb_usuario WHERE matricula=%s", (MAT,)).iloc[0]["ativo"]
    print(f"{i}: {msg} | mem={obter_tentativas(MAT)} | ativo={ativo}")

resetar_tentativas(MAT)
app_dal.update("UPDATE tb_usuario SET ativo=1 WHERE matricula=%s", (MAT,))
print("Teste concluido.")
