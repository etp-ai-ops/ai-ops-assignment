"""Student-owned fixed router-hostname lookup queries."""

from __future__ import annotations

from .query import FixedQueryExecutor
from .result_writer import CsvResult


class HostnameRepository:
    def __init__(self, executor: FixedQueryExecutor) -> None:
        self._executor = executor

    def lookup_router_hostnames(
        self,
        *,
        ip: str | None = None,
        hostname_exact: str | None = None,
        hostname_prefix: str | None = None,
    ) -> CsvResult:
        """Write hostname records selected by exactly one lookup mode."""
        # TODO(student): Reject zero or multiple selectors, then execute one of
        # three fixed Queries. Prefix matching must escape backslash, `%`, and
        # `_` before adding `%`, and SQL must declare ESCAPE '\'.
        raise NotImplementedError("TODO(student): implement lookup_router_hostnames")
