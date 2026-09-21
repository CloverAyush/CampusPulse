import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.logging_config import request_id_var, user_id_var

logger = logging.getLogger("campuspulse.access")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Gives every request a traceable id and emits one access log line per request,
    so a report that 'never arrived' can actually be looked up."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:16]
        request_token = request_id_var.set(request_id)
        user_token = user_id_var.set("-")
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "Request failed",
                extra={"method": request.method, "path": request.url.path,
                       "duration_ms": duration_ms},
            )
            raise
        finally:
            request_id_var.reset(request_token)
            user_id_var.reset(user_token)

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "Request completed",
            extra={"method": request.method, "path": request.url.path,
                   "status_code": response.status_code, "duration_ms": duration_ms},
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        return response
