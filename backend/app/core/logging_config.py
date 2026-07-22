import logging
import sys
import uuid
from contextvars import ContextVar

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = request_id_ctx_var.get()
        except Exception:
            record.request_id = "-"
        return True


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s [req:%(request_id)s] %(message)s"
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    # remove default handlers
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.addFilter(RequestIdFilter())


def new_request_id() -> str:
    return uuid.uuid4().hex
