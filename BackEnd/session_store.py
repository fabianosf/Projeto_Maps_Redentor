# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""
Armazenamento server-side de sessões autenticadas e tokens de troca de senha.

Conforme RF-RN-008 e RF-RN-008a em Doc/Requisitos_Ciclo_Login_MAP.md.
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Optional


SESSION_TTL_SECONDS = 8 * 3600
PASSWORD_CHANGE_TOKEN_TTL_SECONDS = 15 * 60


@dataclass(frozen=True)
class SessionRecord:
    id_usuario: int
    matricula: str
    codigo_perfil: int
    nome: str
    created_at: float
    last_access: float


@dataclass(frozen=True)
class PasswordChangeTokenRecord:
    id_usuario: int
    created_at: float


class SessionStore:
    """Sessões autenticadas em memória (RF-RN-008). Thread-safe."""

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = threading.Lock()

    def create(
        self,
        id_usuario: int,
        matricula: str,
        codigo_perfil: int,
        nome: str,
    ) -> str:
        now = time.time()
        session_id = secrets.token_urlsafe(32)
        record = SessionRecord(
            id_usuario=id_usuario,
            matricula=matricula,
            codigo_perfil=codigo_perfil,
            nome=nome,
            created_at=now,
            last_access=now,
        )
        with self._lock:
            self._purge_expired_unlocked(now)
            self._sessions[session_id] = record
        return session_id

    def get(self, session_id: Optional[str]) -> Optional[SessionRecord]:
        if not session_id:
            return None

        now = time.time()
        with self._lock:
            self._purge_expired_unlocked(now)
            record = self._sessions.get(session_id)
            if record is None:
                return None

            if now - record.last_access > self._ttl:
                del self._sessions[session_id]
                return None

            renewed = SessionRecord(
                id_usuario=record.id_usuario,
                matricula=record.matricula,
                codigo_perfil=record.codigo_perfil,
                nome=record.nome,
                created_at=record.created_at,
                last_access=now,
            )
            self._sessions[session_id] = renewed
            return renewed

    def destroy(self, session_id: Optional[str]) -> bool:
        if not session_id:
            return False
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def destroy_all_for_user(self, id_usuario: int) -> int:
        with self._lock:
            keys = [
                key
                for key, record in self._sessions.items()
                if record.id_usuario == id_usuario
            ]
            for key in keys:
                del self._sessions[key]
            return len(keys)

    def purge_expired(self) -> int:
        with self._lock:
            return self._purge_expired_unlocked(time.time())

    def _purge_expired_unlocked(self, now: float) -> int:
        expired = [
            key
            for key, record in self._sessions.items()
            if now - record.last_access > self._ttl
        ]
        for key in expired:
            del self._sessions[key]
        return len(expired)


class PasswordChangeTokenStore:
    """
    Token temporário para troca de senha no primeiro acesso (RF-RN-008a).
    Não concede acesso à Lista_mapa.
    """

    def __init__(self, ttl_seconds: int = PASSWORD_CHANGE_TOKEN_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._tokens: dict[str, PasswordChangeTokenRecord] = {}
        self._lock = threading.Lock()

    def create(self, id_usuario: int) -> str:
        now = time.time()
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._purge_expired_unlocked(now)
            self._tokens[token] = PasswordChangeTokenRecord(
                id_usuario=id_usuario,
                created_at=now,
            )
        return token

    def get(self, token: Optional[str]) -> Optional[int]:
        if not token:
            return None

        now = time.time()
        with self._lock:
            self._purge_expired_unlocked(now)
            record = self._tokens.get(token)
            if record is None:
                return None
            if now - record.created_at > self._ttl:
                del self._tokens[token]
                return None
            return record.id_usuario

    def consume(self, token: Optional[str]) -> Optional[int]:
        if not token:
            return None

        now = time.time()
        with self._lock:
            self._purge_expired_unlocked(now)
            record = self._tokens.pop(token, None)
            if record is None:
                return None
            if now - record.created_at > self._ttl:
                return None
            return record.id_usuario

    def invalidate(self, token: Optional[str]) -> bool:
        if not token:
            return False
        with self._lock:
            return self._tokens.pop(token, None) is not None

    def invalidate_for_user(self, id_usuario: int) -> int:
        with self._lock:
            keys = [
                key
                for key, record in self._tokens.items()
                if record.id_usuario == id_usuario
            ]
            for key in keys:
                del self._tokens[key]
            return len(keys)

    def purge_expired(self) -> int:
        with self._lock:
            return self._purge_expired_unlocked(time.time())

    def _purge_expired_unlocked(self, now: float) -> int:
        expired = [
            key
            for key, record in self._tokens.items()
            if now - record.created_at > self._ttl
        ]
        for key in expired:
            del self._tokens[key]
        return len(expired)


session_store = SessionStore()
password_change_token_store = PasswordChangeTokenStore()
