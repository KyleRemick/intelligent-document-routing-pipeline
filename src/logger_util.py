"""
Structured logging helpers for CloudWatch.

Logs are JSON-friendly strings: one logical line per log for easier filtering.
Long or sensitive fields should be truncated before logging (see sanitize helpers).
"""

from __future__ import annotations

import json
import logging
from typing import Any

# Lambda runtime configures the root logger; use a named logger for clarity.
LOGGER_NAME = "doc_routing"


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or LOGGER_NAME)


def log_json(logger: logging.Logger, level: int, event: str, fields: dict[str, Any]) -> None:
    """Emit a single JSON object on one line (message body is JSON)."""
    payload = {"event": event, **fields}
    logger.log(level, json.dumps(payload, default=str, ensure_ascii=False))


def truncate_for_log(text: str | None, max_chars: int) -> str:
    """Limit log volume; avoid dumping full OCR output to CloudWatch."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"... [truncated, len={len(text)}]"
