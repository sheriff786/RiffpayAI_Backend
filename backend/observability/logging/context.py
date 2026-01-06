import contextvars
import uuid

request_id_ctx = contextvars.ContextVar("request_id", default="system")

def set_request_id(rid: str | None = None):
    if rid is None:
        rid = str(uuid.uuid4())[:8]
    request_id_ctx.set(rid)
    return rid

def get_request_id():
    return request_id_ctx.get()
