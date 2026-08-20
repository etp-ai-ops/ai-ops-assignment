"""Typed runtime configuration loaded once during application startup."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DB_POOL_MAX = 5
DEFAULT_QUERY_TIMEOUT_MS = 30_000
DEFAULT_OUTPUT_DIR = Path("/app/outputs")
DEFAULT_LOG_LEVEL = "INFO"
MIN_MASTER_KEY_LENGTH = 32
ALLOWED_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})


class ConfigurationError(ValueError):
    """Raised when runtime configuration is missing or unsafe."""


@dataclass(frozen=True, slots=True)
class Settings:
    master_key: str = field(repr=False)
    database_url: str = field(repr=False)
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    db_pool_max: int = DEFAULT_DB_POOL_MAX
    query_timeout_ms: int = DEFAULT_QUERY_TIMEOUT_MS
    output_dir: Path = DEFAULT_OUTPUT_DIR
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        values = os.environ if environ is None else environ
        raw_master_key = values.get("MCP_MASTER_KEY", "")
        master_key = raw_master_key.strip()
        database_url = values.get("DATABASE_URL", "").strip()
        host = values.get("MCP_HOST", "").strip() or DEFAULT_HOST
        output_dir = Path(values.get("OUTPUT_DIR", "").strip() or str(DEFAULT_OUTPUT_DIR))
        log_level = (values.get("LOG_LEVEL", "").strip() or DEFAULT_LOG_LEVEL).upper()
        errors: list[str] = []
        if len(master_key) < MIN_MASTER_KEY_LENGTH:
            errors.append(f"MCP_MASTER_KEY must be at least {MIN_MASTER_KEY_LENGTH} characters")
        if raw_master_key != master_key or any(
            ord(character) < 0x21 or ord(character) > 0x7E for character in master_key
        ):
            errors.append("MCP_MASTER_KEY must contain only visible ASCII characters")
        if not _is_postgresql_url(database_url):
            errors.append("DATABASE_URL must be a postgresql:// or postgres:// URL")
        if not host or any(character.isspace() for character in host):
            errors.append("MCP_HOST must be a non-empty host without whitespace")
        if not output_dir.is_absolute():
            errors.append("OUTPUT_DIR must be an absolute path")
        if log_level not in ALLOWED_LOG_LEVELS:
            errors.append(f"LOG_LEVEL must be one of {', '.join(sorted(ALLOWED_LOG_LEVELS))}")
        port = _integer(values, "MCP_PORT", DEFAULT_PORT, 1, 65_535, errors)
        pool_max = _integer(values, "DB_POOL_MAX", DEFAULT_DB_POOL_MAX, 1, 20, errors)
        timeout = _integer(
            values, "QUERY_TIMEOUT_MS", DEFAULT_QUERY_TIMEOUT_MS, 1, 3_600_000, errors
        )
        if errors:
            raise ConfigurationError("Invalid configuration: " + "; ".join(errors))
        return cls(master_key, database_url, host, port, pool_max, timeout, output_dir, log_level)

    @property
    def log_redaction_values(self) -> tuple[str, ...]:
        return (self.master_key, self.database_url)

    def prepare_output_dir(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError("OUTPUT_DIR cannot be created") from exc
        if not self.output_dir.is_dir() or not os.access(self.output_dir, os.W_OK):
            raise ConfigurationError("OUTPUT_DIR must be a writable directory")


def _integer(
    values: Mapping[str, str],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
    errors: list[str],
) -> int:
    raw = values.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{name} must be an integer")
        return default
    if not minimum <= value <= maximum:
        errors.append(f"{name} must be between {minimum} and {maximum}")
    return value


def _is_postgresql_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return parsed.scheme in {"postgres", "postgresql"} and bool(parsed.path.strip("/"))
