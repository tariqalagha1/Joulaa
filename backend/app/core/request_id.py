import time
import uuid

import structlog

logger = structlog.get_logger()


async def request_id_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)

    response.headers["X-Request-ID"] = request_id
    logger.info(
        f"[REQ {request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
    )
    return response
