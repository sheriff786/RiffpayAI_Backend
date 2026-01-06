import logging
from observability.logging.context import get_request_id

class RequestLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs["extra"] = {"request_id": get_request_id()}
        return msg, kwargs
