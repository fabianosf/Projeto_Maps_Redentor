# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""
Regras de negócio de autenticação (RF-RN-003 a RF-RN-011).

Usado pelos endpoints em auth_routes.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

import bcrypt

from .matricula_validation import matricula_valida
from .session_store import password_change_token_store
from .login_attempt_store import registrar_tentativa_falha, resetar_tentativas
from .CONFIGURACAO import clmain

LOGIN_INVALID_MESSAGE = "Login inválido!"
MATRICULA_INVALIDA_MESSAGE = "Matrícula inválida!"
USUARIO_INVALIDO_MESSAGE = "Usuário inválido!"
LIMITE_TENTATIVAS_MESSAGE = "Limite máximo de tentativas!"
QTD_MAX_TENTATIVAS_CHAVE = "QTD_MAX_TENTATIVAS"
BLOQUEIO_TENTATIVAS_CHAVE = "BLOQUEIO_TENTATIVAS_LOGIN"
QTD_MAX_TENTATIVAS_PADRAO = 3
PASSWORD_MISMATCH_MESSAGE = "Senhas digitadas diferentes!"
PASSWORD_INVALID_MESSAGE = "Senha inválida!"
PASSWORD_SUCCESS_MESSAGE = "senha cadastrada com sucesso!"
GENERIC_ERROR_MESSAGE = "Operação não autorizada."

_SGBD_NOME_EXIBICAO = {
    "mariadb": "MariaDB",
    "mysql": "MariaDB",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "postgree": "PostgreSQL",
    "oracle": "Oracle",
}


def mensagem_db_indisponivel(sgbd: str = "") -> str:
    """Mensagem 503 alinhada ao SGBD configurado (não hardcode MariaDB)."""
    nome = _SGBD_NOME_EXIBICAO.get((sgbd or "").strip().lower(), "banco de dados")
    return f"Banco de dados indisponível. Verifique se o {nome} está em execução."


# Compat: imports antigos / testes que ainda referenciam a constante.
DB_UNAVAILABLE_MESSAGE = mensagem_db_indisponivel("mariadb")

BCRYPT_ROUNDS = 12
# Mín. 8; 1 maiúscula; 1 minúscula; 1 dígito; 1 especial (RF-03 / RF-RN-007).
_PASSWORD_POLICY = re.compile(
    r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]).{8,}$'
)


@dataclass(frozen=True)
class UsuarioAuth:
    id_usuario: int
    matricula: str
    nome: str
    codigo_perfil: int
    trocar_senha: bool
    ativo: bool


@dataclass(frozen=True)
class LoginSuccess:
    usuario: UsuarioAuth
    change_token: Optional[str] = None


@dataclass(frozen=True)
class AuthError:
    mensagem: str
    codigo: str = "auth_error"


def _row_value(row, key: str, default=None):
    if key not in row.index:
        return default
    value = row[key]
    if value is None:
        return default
    return value


def _usuario_from_row(row) -> UsuarioAuth:
    return UsuarioAuth(
        id_usuario=int(_row_value(row, "id_usuario")),
        matricula=str(_row_value(row, "matricula", "")),
        nome=str(_row_value(row, "nome", "")),
        codigo_perfil=int(_row_value(row, "codigo_perfil")),
        trocar_senha=bool(int(_row_value(row, "trocar_senha", 0))),
        ativo=bool(int(_row_value(row, "ativo", 1))),
    )


def buscar_usuario_por_matricula(dal, matricula: str) -> Optional[UsuarioAuth]:
    df = dal.read(
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.senha, u.ativo, u.trocar_senha,
               p.codigo_perfil
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.matricula = ?
        """,
        (matricula.strip(),),
    )
    if df.empty:
        return None

    row = df.iloc[0]
    usuario = _usuario_from_row(row)
    usuario = UsuarioAuth(
        id_usuario=usuario.id_usuario,
        matricula=usuario.matricula,
        nome=usuario.nome,
        codigo_perfil=usuario.codigo_perfil,
        trocar_senha=usuario.trocar_senha,
        ativo=usuario.ativo,
    )
    return usuario


def buscar_hash_senha(dal, matricula: str) -> Optional[str]:
    df = dal.read(
        "SELECT senha FROM tb_usuario WHERE matricula = ?",
        (matricula.strip(),),
    )
    if df.empty:
        return None
    return str(df.iloc[0]["senha"])


def buscar_usuario_por_id(dal, id_usuario: int) -> Optional[UsuarioAuth]:
    df = dal.read(
        """
        SELECT u.id_usuario, u.matricula, u.nome, u.ativo, u.trocar_senha,
               p.codigo_perfil
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.id_usuario = ?
        """,
        (id_usuario,),
    )
    if df.empty:
        return None
    return _usuario_from_row(df.iloc[0])


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            senha_plana.encode("utf-8"),
            senha_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def hash_senha(senha_plana: str) -> str:
    hashed = bcrypt.hashpw(
        senha_plana.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    )
    return hashed.decode("utf-8")


def obter_qtd_max_tentativas(dal) -> int:
    """Lê QTD_MAX_TENTATIVAS em tb_configuracao via CONFIGURACAO.py."""
    cfg = clmain(dal)
    if not cfg._pesquisar_Chave_Configuracao(QTD_MAX_TENTATIVAS_CHAVE):
        return QTD_MAX_TENTATIVAS_PADRAO
    valor = cfg._obter_Valor_Configuracao(QTD_MAX_TENTATIVAS_CHAVE)
    if not valor or not str(valor).strip().isdigit():
        return QTD_MAX_TENTATIVAS_PADRAO
    qtd = int(str(valor).strip())
    return qtd if qtd > 0 else QTD_MAX_TENTATIVAS_PADRAO


def bloqueio_tentativas_ativo(dal) -> bool:
    cfg = clmain(dal)
    if not cfg._pesquisar_Chave_Configuracao(BLOQUEIO_TENTATIVAS_CHAVE):
        return True
    return cfg._obter_Valor_Configuracao(BLOQUEIO_TENTATIVAS_CHAVE) == "1"


def _inativar_usuario(dal, id_usuario: int) -> bool:
    return bool(
        dal.update(
            "UPDATE tb_usuario SET ativo = FALSE WHERE id_usuario = ?",
            (id_usuario,),
        )
    )


def validar_nova_senha(nova_senha: str, confirmacao: str) -> Optional[str]:
    if nova_senha != confirmacao:
        return PASSWORD_MISMATCH_MESSAGE
    if not _PASSWORD_POLICY.match(nova_senha or ""):
        return PASSWORD_INVALID_MESSAGE
    return None


def autenticar_login(dal, matricula: str, senha: str) -> LoginSuccess | AuthError:
    if not matricula_valida(matricula):
        return AuthError(mensagem=MATRICULA_INVALIDA_MESSAGE, codigo="matricula_invalida")
    if not senha:
        return AuthError(mensagem=PASSWORD_INVALID_MESSAGE, codigo="senha_invalida")
    # Política forte (_PASSWORD_POLICY) vale na troca/cadastro de senha definitiva,
    # não no login — senha provisória/admin curta (ex.: "123") precisa autenticar.

    usuario = buscar_usuario_por_matricula(dal, matricula)
    if usuario is None or not usuario.ativo:
        return AuthError(mensagem=USUARIO_INVALIDO_MESSAGE, codigo="usuario_invalido")

    hash_senha_db = buscar_hash_senha(dal, matricula)
    if hash_senha_db is None:
        return AuthError(mensagem=USUARIO_INVALIDO_MESSAGE, codigo="usuario_invalido")

    if not verificar_senha(senha, hash_senha_db):
        if bloqueio_tentativas_ativo(dal):
            max_tentativas = obter_qtd_max_tentativas(dal)
            tentativas = registrar_tentativa_falha(usuario.matricula)
            if tentativas >= max_tentativas:
                _inativar_usuario(dal, usuario.id_usuario)
                resetar_tentativas(usuario.matricula)
                return AuthError(
                    mensagem=LIMITE_TENTATIVAS_MESSAGE,
                    codigo="limite_tentativas",
                )
        return AuthError(mensagem=PASSWORD_INVALID_MESSAGE, codigo="senha_invalida")

    resetar_tentativas(usuario.matricula)

    change_token = None
    if usuario.trocar_senha:
        password_change_token_store.invalidate_for_user(usuario.id_usuario)
        change_token = password_change_token_store.create(usuario.id_usuario)

    return LoginSuccess(usuario=usuario, change_token=change_token)


def trocar_senha(
    dal,
    change_token: str,
    nova_senha: str,
    confirmacao_senha: str,
) -> AuthError | dict[str, Any]:
    erro_validacao = validar_nova_senha(nova_senha, confirmacao_senha)
    if erro_validacao:
        return AuthError(mensagem=erro_validacao, codigo="validacao_senha")

    id_usuario = password_change_token_store.consume(change_token)
    if id_usuario is None:
        return AuthError(mensagem=GENERIC_ERROR_MESSAGE, codigo="token_invalido")

    usuario = buscar_usuario_por_id(dal, id_usuario)
    if usuario is None or not usuario.ativo:
        return AuthError(mensagem=GENERIC_ERROR_MESSAGE, codigo="token_invalido")

    novo_hash = hash_senha(nova_senha)
    ok = dal.update(
        """
        UPDATE tb_usuario
        SET senha = ?, trocar_senha = FALSE
        WHERE id_usuario = ?
        """,
        (novo_hash, id_usuario),
    )
    if not ok:
        return AuthError(mensagem=GENERIC_ERROR_MESSAGE, codigo="persistencia")

    password_change_token_store.invalidate_for_user(id_usuario)
    return {"ok": True, "mensagem": PASSWORD_SUCCESS_MESSAGE}


def cancelar_troca_senha(change_token: Optional[str]) -> dict[str, bool]:
    if change_token:
        password_change_token_store.invalidate(change_token)
    return {"ok": True}


def usuario_publico(usuario: UsuarioAuth) -> dict[str, Any]:
    return {
        "id_usuario": usuario.id_usuario,
        "matricula": usuario.matricula,
        "nome": usuario.nome,
        "codigo_perfil": usuario.codigo_perfil,
        "trocar_senha": usuario.trocar_senha,
    }
