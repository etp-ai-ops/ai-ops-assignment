"""Compact JSON logging with registered-secret redaction."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_FIELDS = frozenset({"authorization", "database_url", "password", "token", "secret"})
BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)[^\s,;]+")
POSTGRES_PATTERN = re.compile(r"(?i)(postgres(?:ql)?://[^:/\s]+:)[^@\s]+(@)")


def redact(value: Any, *, field_name: str | None = None) -> Any:
    if field_name is not None and field_name.lower() in SENSITIVE_FIELDS:
        return REDACTED
    if isinstance(value, Mapping):
        return {str(key): redact(item, field_name=str(key)) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return POSTGRES_PATTERN.sub(rf"\1{REDACTED}\2", BEARER_PATTERN.sub(rf"\1{REDACTED}", value))
    if value is None or isinstance(value, bool | int | float):
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    def __init__(self, secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self._secrets = tuple(secret for secret in secrets if secret)

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        for name in ("event", "context"):
            if hasattr(record, name):
                payload[name] = redact(getattr(record, name))
        serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        for secret in self._secrets:
            serialized = serialized.replace(secret, REDACTED)
        return serialized


def configure_logging(level: str, *, secrets: tuple[str, ...] = ()) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(secrets))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("mcp").setLevel(logging.CRITICAL)
