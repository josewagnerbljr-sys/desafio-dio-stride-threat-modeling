"""
Logging estruturado em JSON.

Em produção, logs em JSON são o padrão esperado por qualquer stack de
observabilidade (Azure Monitor, ELK, Datadog etc.) — permitem consultar e
correlacionar eventos em vez de fazer grep em texto solto.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class FormatadorJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extras = getattr(record, "extra_fields", None)
        if extras:
            payload.update(extras)
        return json.dumps(payload, ensure_ascii=False)


def configurar_logging(nivel: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(FormatadorJSON())

    root = logging.getLogger()
    root.setLevel(nivel)
    root.handlers = [handler]

    # Silencia verbosidade excessiva de libs de terceiros
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def novo_request_id() -> str:
    return uuid.uuid4().hex[:12]
