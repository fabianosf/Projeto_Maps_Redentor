# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Auditoria imutável (APPEND-ONLY) — P1."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from flask import g, has_request_context, request

TZ_SP = ZoneInfo("America/Sao_Paulo")


def _correlation_id() -> str:
    if has_request_context():
        existing = getattr(g, "correlation_id", None)
        if existing:
            return str(existing)
        hdr = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if hdr and str(hdr).strip():
            cid = str(hdr).strip()[:64]
            g.correlation_id = cid
            return cid
        cid = uuid.uuid4().hex[:32]
        g.correlation_id = cid
        return cid
    return uuid.uuid4().hex[:32]


def _origem_ip() -> Optional[str]:
    if not has_request_context():
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.remote_addr or "")[:64] or None


def _json_dump(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"repr": str(value)}, ensure_ascii=False)


def registrar_auditoria(
    dal,
    *,
    entidade: str,
    acao: str,
    id_entidade: str | int | None = None,
    id_executor: int | None = None,
    perfil_executor: int | None = None,
    valores_antes: Any = None,
    valores_depois: Any = None,
    motivo: str | None = None,
) -> None:
    """
    Insere registro imutável. Falhas de auditoria não devem derrubar a operação
    principal — loga e segue (best-effort), exceto correções excepcionais que
    devem validar o insert no caller.
    """
    try:
        agora = datetime.now(TZ_SP).replace(tzinfo=None)
        dal.create(
            """
            INSERT INTO tb_auditoria (
                entidade, id_entidade, acao, id_executor, perfil_executor,
                criado_em, tz, correlation_id, origem_ip,
                valores_antes, valores_depois, motivo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(entidade)[:60],
                str(id_entidade)[:60] if id_entidade is not None else None,
                str(acao)[:60],
                int(id_executor) if id_executor is not None else None,
                int(perfil_executor) if perfil_executor is not None else None,
                agora.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "America/Sao_Paulo",
                _correlation_id(),
                _origem_ip(),
                _json_dump(valores_antes),
                _json_dump(valores_depois),
                (str(motivo).strip()[:500] if motivo else None),
            ),
        )
    except Exception:
        # Tabela pode ainda não existir em ambientes sem migrate P1.
        pass


def registrar_acesso_negado(
    dal,
    *,
    entidade: str,
    id_entidade: str | int | None,
    id_executor: int | None,
    perfil_executor: int | None,
    motivo: str,
) -> None:
    registrar_auditoria(
        dal,
        entidade=entidade,
        acao="acesso_negado",
        id_entidade=id_entidade,
        id_executor=id_executor,
        perfil_executor=perfil_executor,
        motivo=motivo,
    )
