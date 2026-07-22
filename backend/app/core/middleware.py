import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import new_request_id, request_id_ctx_var
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        rid_header = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        if not rid_header:
            rid = new_request_id()
        else:
            rid = rid_header
        # set context var for logging
        request_id_ctx_var.set(rid)
        response = await call_next(request)
        # expose request id to client
        response.headers.setdefault("X-Request-ID", rid)
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        start = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            logger.info("%s %s %s %.2fms", request.method, request.url.path, status_code, elapsed)
        return response
