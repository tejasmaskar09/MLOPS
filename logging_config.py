"""
Experiment 3: Structured Logging Configuration
================================================
- Configures JSON-structured logging for every request/response
- Generates unique request IDs for traceability
"""

import logging
import json
import uuid
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach extra fields if present
        for key in ("request_id", "method", "path", "status_code", "duration_ms",
                     "client_ip", "error_type", "error_detail"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("mlops_api")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


def generate_request_id() -> str:
    """Return a short unique request identifier."""
    return uuid.uuid4().hex[:12]
