# from starlette.middleware.base import BaseHTTPMiddleware
# from observability.logging.context import set_request_id
# from observability.logging.logger import get_logger
# # from observability.logging.adapters import RequestLogger
# from observability.logging.llm_ada import RequestLogger

# base_logger = get_logger("api", "app.log")
# logger = RequestLogger(base_logger, {})

# class RequestLoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request, call_next):
#         rid = set_request_id()
#         logger.info(f"START {request.method} {request.url.path}")

#         response = await call_next(request)

#         logger.info(f"END status={response.status_code}")
#         return response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from observability.logging.context import set_request_id
from observability.logging.logger import get_logger
# from observability.logging.adapters import RequestLogger
from observability.logging.llm_ada import RequestLogger
logger = logging.getLogger("request")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()

        request.state.request_id = request_id

        logger.info(
            f"START {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )

        response = await call_next(request)

        duration = round(time.time() - start_time, 3)

        logger.info(
            f"END {request.method} {request.url.path} "
            f"status={response.status_code} time={duration}s",
            extra={"request_id": request_id}
        )

        response.headers["X-Request-ID"] = request_id
        return response
