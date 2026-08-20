"""Conservative PostgreSQL connection pool with defense-in-depth settings."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final

from psycopg import Connection
from psycopg_pool import ConnectionPool

from ..config import Settings

APPLICATION_NAME: Final = "nids-itdk-mcp"
DEFAULT_LOCK_TIMEOUT_MS: Final = 5_000


class DatabasePool:
    """Own a small pool whose sessions begin read-only and time-bounded."""

    def __init__(self, database_url: str, *, max_size: int, query_timeout_ms: int) -> None:
        lock_timeout_ms = min(DEFAULT_LOCK_TIMEOUT_MS, query_timeout_ms)
        options = " ".join(
            (
                "-c default_transaction_read_only=on",
                f"-c statement_timeout={query_timeout_ms}",
                f"-c lock_timeout={lock_timeout_ms}",
            )
        )
        self._pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=max_size,
            open=False,
            timeout=5.0,
            kwargs={
                "application_name": APPLICATION_NAME,
                "autocommit": False,
                "options": options,
            },
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> DatabasePool:
        return cls(
            settings.database_url,
            max_size=settings.db_pool_max,
            query_timeout_ms=settings.query_timeout_ms,
        )

    def open(self) -> None:
        self._pool.open()

    def close(self) -> None:
        self._pool.close()

    def check(self) -> None:
        with self._pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

    @contextmanager
    def connection(self) -> Iterator[Connection[tuple[object, ...]]]:
        with self._pool.connection() as connection:
            yield connection
