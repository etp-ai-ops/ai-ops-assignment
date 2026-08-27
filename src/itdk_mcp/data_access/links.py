"""Fixed link endpoint queries.

``get_link_endpoints`` is complete and is the worked example of the fixed,
parameterized query pattern. The student-built ``find_router_links_between_asns``
lives in ``itdk_mcp/student_tools.py`` and defines its own column metadata,
since its projection (``link_id, node_a, node_b``) differs from this module's.
"""

from __future__ import annotations

from psycopg import sql

from .query import FixedQueryExecutor, Query
from .result_writer import Column, CsvResult

LINK_COLUMNS = (
    Column("link_id", "string"),
    Column("endpoint_ordinal", "int32"),
    Column("endpoint_token", "string"),
    Column("node_id", "string"),
)

_GET_LINK_ENDPOINTS = Query(
    sql.SQL("""
        SELECT link_id, endpoint_ordinal, endpoint_token, node_id
        FROM caida_itdk.itdk_link_endpoints
        WHERE link_id = %s
        ORDER BY endpoint_ordinal
    """),
    LINK_COLUMNS,
    "get_link_endpoints",
)


class LinkRepository:
    def __init__(self, executor: FixedQueryExecutor) -> None:
        self._executor = executor

    def get_link_endpoints(self, link_id: str) -> CsvResult:
        """Fully worked example of a fixed, parameterized repository query."""
        return self._executor.execute(_GET_LINK_ENDPOINTS, (link_id,))
