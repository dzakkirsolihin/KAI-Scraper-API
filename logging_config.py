
import logging
import sys
import structlog
from structlog.types import EventDict
from typing import Any

def setup_logging(log_level: str = "INFO"):
    """
    Konfigurasi logging terstruktur menggunakan structlog.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level.upper(),
    )

    # Prosesor custom: menambahkan nama logger ke setiap event log
    def add_logger_name(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
        event_dict['logger'] = logger.name
        return event_dict

    # Konfigurasi rantai prosesor structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # Gabungkan context vars jika ada
            structlog.stdlib.add_log_level,           # Tambahkan level log
            add_logger_name,                          # Tambahkan nama logger
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,               # Render exception info jika ada
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),      # Output log dalam format JSON
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )