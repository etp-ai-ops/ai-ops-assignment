"""Fixed router-hostname lookup queries.

Complete, worked example of the mutually-exclusive-selector pattern from
Safe-Queries.md Sections 6-7: exactly one of ``ip``, ``hostname_exact``, or
``hostname_prefix`` selects one of three fixed, parameterized queries, and
prefix matching escapes backslash, then ``%``, then ``_`` before appending
the server-owned trailing wildcard.
"""

from __future__ import annotations

from psycopg import sql

from .query import FixedQueryExecutor, Query
from .result_writer import Column, CsvResult

HOSTNAME_COLUMNS = (
    Column("ip", "inet"),
    Column("hostname", "string"),
)

_LOOKUP_BY_IP = Query(
    sql.SQL("""
        SELECT ip, hostname
        FROM caida_itdk.itdk_router_hostnames
        WHERE ip = %s
        ORDER BY ip, hostname NULLS FIRST
    """),
    HOSTNAME_COLUMNS,
    "lookup_router_hostnames_by_ip",
)

_LOOKUP_BY_EXACT_HOSTNAME = Query(
    sql.SQL("""
        SELECT ip, hostname
        FROM caida_itdk.itdk_router_hostnames
        WHERE hostname = %s
        ORDER BY hostname, ip
    """),
    HOSTNAME_COLUMNS,
    "lookup_router_hostnames_by_exact",
)

_LOOKUP_BY_HOSTNAME_PREFIX = Query(
    sql.SQL("""
        SELECT ip, hostname
        FROM caida_itdk.itdk_router_hostnames
        WHERE hostname LIKE %s ESCAPE '\\'
        ORDER BY hostname, ip
    """),
    HOSTNAME_COLUMNS,
    "lookup_router_hostnames_by_prefix",
)


def _escape_like_prefix(prefix: str) -> str:
    """Escape backslash, then ``%``, then ``_``, then append the server wildcard."""
    escaped = prefix.replace("\\", "\\\\")
    escaped = escaped.replace("%", "\\%")
    escaped = escaped.replace("_", "\\_")
    return f"{escaped}%"


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
        selectors = [value for value in (ip, hostname_exact, hostname_prefix) if value is not None]
        if len(selectors) != 1:
            raise ValueError(
                "lookup_router_hostnames requires exactly one of ip, hostname_exact, "
                "hostname_prefix"
            )
        if ip is not None:
            return self._executor.execute(_LOOKUP_BY_IP, (ip,))
        if hostname_exact is not None:
            return self._executor.execute(_LOOKUP_BY_EXACT_HOSTNAME, (hostname_exact,))
        assert hostname_prefix is not None
        return self._executor.execute(
            _LOOKUP_BY_HOSTNAME_PREFIX, (_escape_like_prefix(hostname_prefix),)
        )
