"""Centralized logging configuration with rotating file handler and structured JSON output."""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from app.config import settings


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging.
    Supports extra context fields passed via the `extra` dict.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Include extra context fields (user_id, conversation_id, elapsed_ms, etc.)
        for key in ("user_id", "conversation_id", "elapsed_ms", "intent",
                     "tool", "error", "status_code", "path", "response_time_ms",
                     "predicted_cases", "request_id"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure application-wide logging with rotating file output."""
    root_logger = logging.getLogger()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # ── Console handler ────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(console_handler)

    # ── Rotating file handler ──────────────────────────────────
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not settings.DATABASE_ECHO else logging.DEBUG
    )

    root_logger.info(
        "Logging configured",
        extra={"level": settings.LOG_LEVEL, "format": settings.LOG_FORMAT, "file": settings.LOG_FILE},
    )


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
