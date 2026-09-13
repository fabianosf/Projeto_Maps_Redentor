# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Observabilidade — correlation ID, logs estruturados, métricas leves em memória."""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import defaultdict
from typing import Any

from flask import Flask, Response, g, has_request_context, jsonify, request

logger = logging.getLogger("redmapa")

_metrics_lock = threading.Lock()
_metrics: dict[str, Any] = {
    "requests_total": 0,
    "errors_5xx": 0,
    "errors_4xx": 0,
    "latency_ms_sum": 0.0,
    "latency_ms_count": 0,
    "erp_failures": 0,
    "by_path": defaultdict(int),
}


def ensure_correlation_id() -> str:
    if has_request_context():
        existing = getattr(g, "correlation_id", None)
        if existing:
            return str(existing)
        hdr = request.headers.get("X-Request-ID") or request.headers.get(
            "X-Correlation-ID"
        )
        cid = (str(hdr).strip()[:64] if hdr else uuid.uuid4().hex[:32])
        g.correlation_id = cid
        return cid
    return uuid.uuid4().hex[:32]


def record_erp_failure() -> None:
    with _metrics_lock:
        _metrics["erp_failures"] += 1


def metrics_snapshot() -> dict[str, Any]:
    with _metrics_lock:
        count = max(1, int(_metrics["latency_ms_count"]))
        return {
            "requests_total": _metrics["requests_total"],
            "errors_4xx": _metrics["errors_4xx"],
            "errors_5xx": _metrics["errors_5xx"],
            "erp_failures": _metrics["erp_failures"],
            "latency_ms_avg": round(
                float(_metrics["latency_ms_sum"]) / count, 2
            ),
            "top_paths": dict(
                sorted(
                    _metrics["by_path"].items(),
                    key=lambda kv: kv[1],
                    reverse=True,
                )[:20]
            ),
        }


def init_observability(app: Flask) -> None:
    """Middleware de correlation ID + contadores básicos."""

    @app.before_request
    def _before():
        g.correlation_id = ensure_correlation_id()
        g._req_started = time.perf_counter()

    @app.after_request
    def _after(response: Response) -> Response:
        cid = ensure_correlation_id()
        response.headers.setdefault("X-Request-ID", cid)
        started = getattr(g, "_req_started", None)
        elapsed_ms = (
            (time.perf_counter() - started) * 1000.0 if started is not None else 0.0
        )
        status = int(response.status_code)
        path = request.path or "/"
        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["latency_ms_sum"] += elapsed_ms
            _metrics["latency_ms_count"] += 1
            _metrics["by_path"][path] += 1
            if 400 <= status < 500:
                _metrics["errors_4xx"] += 1
            elif status >= 500:
                _metrics["errors_5xx"] += 1
        if status >= 500:
            logger.error(
                "api_error status=%s path=%s method=%s correlation_id=%s latency_ms=%.1f",
                status,
                path,
                request.method,
                cid,
                elapsed_ms,
            )
        elif status >= 400 and path.startswith("/api/"):
            logger.warning(
                "api_client_error status=%s path=%s method=%s correlation_id=%s",
                status,
                path,
                request.method,
                cid,
            )
        return response

    @app.errorhandler(429)
    def _rate_limited(exc):  # noqa: ARG001
        return (
            jsonify(
                {
                    "ok": False,
                    "codigo": "rate_limit",
                    "mensagem": "Muitas tentativas. Aguarde um momento e tente novamente.",
                    "correlation_id": ensure_correlation_id(),
                }
            ),
            429,
        )

    @app.errorhandler(500)
    def _internal(exc):  # noqa: ARG001
        logger.exception(
            "unhandled_500 correlation_id=%s path=%s",
            ensure_correlation_id(),
            request.path if has_request_context() else "-",
        )
        # Nunca devolve stack trace ao cliente
        return (
            jsonify(
                {
                    "ok": False,
                    "codigo": "erro_interno",
                    "mensagem": "Ocorreu um erro interno. Tente novamente ou contate o suporte.",
                    "correlation_id": ensure_correlation_id(),
                }
            ),
            500,
        )

    @app.get("/api/v1/metrics")
    def metrics():
        """Métricas leves — restringir em produção via rede/proxy."""
        if os.getenv("REDMAPA_METRICS_PUBLIC", "0").lower() not in (
            "1",
            "true",
            "yes",
        ):
            # Em produção, preferir acesso só pela rede interna; ainda assim
            # exigimos flag explícita para expor.
            token = os.getenv("REDMAPA_METRICS_TOKEN", "").strip()
            given = request.headers.get("X-Metrics-Token", "").strip()
            if not token or given != token:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "codigo": "nao_autorizado",
                            "mensagem": "Métricas não disponíveis.",
                            "correlation_id": ensure_correlation_id(),
                        }
                    ),
                    403,
                )
        return jsonify({"ok": True, "metrics": metrics_snapshot()}), 200
