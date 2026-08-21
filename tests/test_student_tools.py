"""Executable specifications for the three student-owned MCP tools.

See ``src/itdk_mcp/student_tools.py`` for the schema, description, and query
body of each tool.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from itdk_mcp.data_access import CsvResult
from itdk_mcp.data_access.query import Query
from itdk_mcp.mcp_tools import TOOL_DESCRIPTIONS, TOOL_SCHEMAS
from itdk_mcp.student_tools import (
    find_hostnames_for_asn,
    find_links_for_node,
    find_peer_asns_for_node,
)

pytestmark = [pytest.mark.student]


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[Query, tuple[object, ...]]] = []

    def execute(self, query: Query, parameters: tuple[object, ...]) -> CsvResult:
        self.calls.append((query, parameters))
        return CsvResult(Path("/output/result.csv"), 0, query.columns)


def _valid(schema: dict[str, object], instance: object) -> bool:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return next(validator.iter_errors(instance), None) is None


def _normalized(query: Query) -> str:
    return " ".join(query.statement.as_string().split())


# ---------------------------------------------------------------------------
# find_links_for_node(node_id) -> link_id, endpoint_ordinal, endpoint_token,
# node_id ordered by (link_id, endpoint_ordinal).
# ---------------------------------------------------------------------------


def test_find_links_for_node_is_a_discoverable_tool() -> None:
    assert "find_links_for_node" in TOOL_SCHEMAS
    assert "find_links_for_node" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["find_links_for_node"]
    assert _valid(schema, {"node_id": "N1"})
    assert not _valid(schema, {})
    assert not _valid(schema, {"node_id": "N1", "order_by": "random()"})


def test_find_links_for_node_repository_is_fixed_and_stably_ordered() -> None:
    executor = RecordingExecutor()
    find_links_for_node(executor, "N1")
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == ("N1",)
    assert "FROM caida_itdk.itdk_link_endpoints" in statement
    assert "WHERE node_id = %s" in statement
    assert "ORDER BY link_id, endpoint_ordinal" in statement
    assert [column.name for column in query.columns] == [
        "link_id", "endpoint_ordinal", "endpoint_token", "node_id"
    ]


# ---------------------------------------------------------------------------
# find_peer_asns_for_node(node_id) -> DISTINCT peer_node_id, peer_asn,
# peer_method ordered by (peer_node_id, peer_asn).
# ---------------------------------------------------------------------------


def test_find_peer_asns_for_node_is_a_discoverable_tool() -> None:
    assert "find_peer_asns_for_node" in TOOL_SCHEMAS
    assert "find_peer_asns_for_node" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["find_peer_asns_for_node"]
    assert _valid(schema, {"node_id": "N2"})
    assert not _valid(schema, {})
    assert not _valid(schema, {"node_id": "N2", "raw_sql": "SELECT 1"})


def test_find_peer_asns_for_node_query_self_joins_links_and_as_assignments() -> None:
    executor = RecordingExecutor()
    find_peer_asns_for_node(executor, "N2")
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == ("N2",)
    assert "DISTINCT" in statement
    assert "FROM caida_itdk.itdk_link_endpoints" in statement
    assert "JOIN caida_itdk.itdk_link_endpoints" in statement
    assert "JOIN caida_itdk.itdk_node_as" in statement
    assert "node_id <>" in statement
    assert "ORDER BY peer_node_id, peer_asn" in statement
    assert [column.name for column in query.columns] == [
        "peer_node_id", "peer_asn", "peer_method"
    ]


# ---------------------------------------------------------------------------
# find_hostnames_for_asn(asn) -> DISTINCT node_id, ip, hostname ordered by
# (node_id, ip NULLS FIRST, hostname).
# ---------------------------------------------------------------------------


def test_find_hostnames_for_asn_is_a_discoverable_tool() -> None:
    assert "find_hostnames_for_asn" in TOOL_SCHEMAS
    assert "find_hostnames_for_asn" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["find_hostnames_for_asn"]
    assert _valid(schema, {"asn": 64500})
    assert not _valid(schema, {"asn": 0})
    assert not _valid(schema, {"asn": "64500"})
    assert not _valid(schema, {})


def test_find_hostnames_for_asn_query_parses_endpoint_token_and_joins_hostnames() -> None:
    executor = RecordingExecutor()
    find_hostnames_for_asn(executor, 64500)
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == (64500,)
    assert "DISTINCT" in statement
    assert "FROM caida_itdk.itdk_node_as" in statement
    assert "JOIN caida_itdk.itdk_link_endpoints" in statement
    assert "JOIN caida_itdk.itdk_router_hostnames" in statement
    # split_part(endpoint_token, ':', 2) truncates IPv6 tokens like
    # "N1:2001:db8:1::1" down to just "2001" and fails the ::inet cast; the
    # working pattern finds the first colon and takes everything after it.
    assert "split_part" not in statement
    assert "strpos" in statement
    assert "::inet" in statement
    assert "ORDER BY" in statement and "NULLS FIRST" in statement
    assert [column.name for column in query.columns] == ["node_id", "ip", "hostname"]


# ---------------------------------------------------------------------------
# One test of my own per tool, below this line.
# ---------------------------------------------------------------------------


def test_find_links_for_node_binds_node_id_and_never_interpolates_it() -> None:
    """Catches an f-string/`.format()` regression splicing node_id into the SQL text."""
    executor = RecordingExecutor()
    injection_like = "N1'; DROP TABLE caida_itdk.itdk_link_endpoints; --"
    find_links_for_node(executor, injection_like)
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert statement.count("%s") == 1
    assert parameters == (injection_like,)
    assert injection_like not in statement


def test_find_peer_asns_for_node_excludes_the_seed_nodes_own_as_rows() -> None:
    """Catches a dropped `e2.node_id <> e1.node_id` predicate that would report
    the seed node's own ASNs as if they were peers."""
    executor = RecordingExecutor()
    find_peer_asns_for_node(executor, "N2")
    query, _parameters = executor.calls[-1]
    statement = _normalized(query)
    assert "e2.node_id <> e1.node_id" in statement
    assert "e1.node_id = %s" in statement


def test_find_hostnames_for_asn_uses_inner_joins_not_left_joins() -> None:
    """Catches a LEFT JOIN swap that would silently report excluded interfaces
    with a null hostname instead of omitting them, changing the tool's contract."""
    executor = RecordingExecutor()
    find_hostnames_for_asn(executor, 64500)
    query, _parameters = executor.calls[-1]
    statement = _normalized(query)
    assert "LEFT JOIN" not in statement
    assert statement.count("JOIN") == 2
