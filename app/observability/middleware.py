"""Middleware de observabilidade: request-id, log estruturado de acesso e duração."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx

logger = logging.getLogger("iris_api.access")


class RequestContextLogMiddleware(BaseHTTPMiddleware):
    """Atribui um request_id a cada requisição e loga método, rota, status e latência.

    O request_id é propagado via `ContextVar` para que qualquer log emitido
    durante o processamento da requisição (mesmo em código de mais baixo
    nível) carregue o mesmo identificador, permitindo correlacionar todos os
    eventos de uma requisição em ferramentas como Grafana/Loki ou Datadog.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_id = request.headers.get("x-request-id")
        request_id = incoming_id or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "http_method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            request_id_ctx.reset(token)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "http_method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
