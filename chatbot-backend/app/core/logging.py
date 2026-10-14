import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """Format logs as JSON objects for structured logging in deployed environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging(debug: bool = False, structured: bool = False) -> logging.Logger:
    """Configure the application logger. DEBUG must actually enable DEBUG output."""
    log_level = logging.DEBUG if debug else logging.INFO
    app_logger = logging.getLogger("travelogix")
    app_logger.setLevel(log_level)

    # Avoid duplicate handlers if called multiple times
    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        if structured:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
        app_logger.addHandler(handler)

    app_logger.propagate = False
    return app_logger


_settings = get_settings()
logger = setup_logging(debug=_settings.DEBUG, structured=_settings.is_production)
