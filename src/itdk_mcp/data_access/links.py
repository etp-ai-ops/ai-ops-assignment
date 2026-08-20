"""Fixed link endpoint queries and the student vertical-slice extension."""

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

    def find_links_for_node(self, node_id: str) -> CsvResult:
        """Write all link-endpoint records that contain ``node_id``."""
        # TODO(student): Complete this vertical slice by defining a fixed Query
        # above and executing it here. Preserve LINK_COLUMNS and stable ordering
        # by link_id then endpoint_ordinal. Never interpolate node_id into SQL.
        raise NotImplementedError("TODO(student): implement find_links_for_node")
