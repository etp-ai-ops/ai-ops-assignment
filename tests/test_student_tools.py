"""Executable specifications for the three student-owned MCP tools.

These tests are expected failures in the distributed starter: none of
``get_node_geolocation``, ``find_router_links_between_asns``, or
``count_nodes_by_asn_and_country`` has a schema, a description, or a query
body yet -- see ``src/itdk_mcp/student_tools.py`` for the ``TODO(student)``
markers and the intended reference SQL for each. Remove the module-level
``xfail`` marker after implementing the tool(s) you build, then add at least
one meaningful test of your own per tool to this file.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from itdk_mcp.data_access import CsvResult
from itdk_mcp.data_access.query import Query
from itdk_mcp.mcp_tools import TOOL_DESCRIPTIONS, TOOL_SCHEMAS
from itdk_mcp.student_tools import (
    count_nodes_by_asn_and_country,
    find_router_links_between_asns,
    get_node_geolocation,
)

pytestmark = [
    pytest.mark.student,
    pytest.mark.xfail(reason="starter TODO(student) implementation", strict=False),
]


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
# get_node_geolocation(node_id) -> node_id, continent, country, region, city,
# latitude, longitude, method, ordered by node_id.
# ---------------------------------------------------------------------------


def test_get_node_geolocation_is_a_discoverable_tool() -> None:
    assert "get_node_geolocation" in TOOL_SCHEMAS
    assert "get_node_geolocation" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["get_node_geolocation"]
    assert _valid(schema, {"node_id": "N1"})
    assert not _valid(schema, {})
    assert not _valid(schema, {"node_id": "N1", "order_by": "random()"})


def test_get_node_geolocation_repository_is_fixed_and_stably_ordered() -> None:
    executor = RecordingExecutor()
    get_node_geolocation(executor, "N1")
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == ("N1",)
    assert "FROM caida_itdk.itdk_node_geolocation" in statement
    assert "WHERE node_id = %s" in statement
    assert "ORDER BY node_id" in statement
    assert [column.name for column in query.columns] == [
        "node_id", "continent", "country", "region", "city",
        "latitude", "longitude", "method",
    ]


# ---------------------------------------------------------------------------
# find_router_links_between_asns(asn_a, asn_b) -> link_id, node_a, node_b,
# ordered by (link_id, node_a, node_b).
# ---------------------------------------------------------------------------


def test_find_router_links_between_asns_is_a_discoverable_tool() -> None:
    assert "find_router_links_between_asns" in TOOL_SCHEMAS
    assert "find_router_links_between_asns" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["find_router_links_between_asns"]
    assert _valid(schema, {"asn_a": 3356, "asn_b": 2906})
    assert not _valid(schema, {"asn_a": 3356})
    assert not _valid(schema, {})
    assert not _valid(schema, {"asn_a": 3356, "asn_b": 2906, "raw_sql": "SELECT 1"})


def test_find_router_links_between_asns_query_self_joins_link_endpoints() -> None:
    executor = RecordingExecutor()
    find_router_links_between_asns(executor, 3356, 2906)
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == (3356, 2906)
    assert "FROM caida_itdk.itdk_link_endpoints" in statement
    assert "JOIN caida_itdk.itdk_link_endpoints" in statement
    assert "FROM caida_itdk.itdk_node_as" in statement
    assert "node_id <>" in statement
    assert "ORDER BY" in statement and "link_id" in statement
    assert [column.name for column in query.columns] == ["link_id", "node_a", "node_b"]


# ---------------------------------------------------------------------------
# count_nodes_by_asn_and_country(asn) -> country, node_count, ordered by
# (node_count DESC, country).
# ---------------------------------------------------------------------------


def test_count_nodes_by_asn_and_country_is_a_discoverable_tool() -> None:
    assert "count_nodes_by_asn_and_country" in TOOL_SCHEMAS
    assert "count_nodes_by_asn_and_country" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["count_nodes_by_asn_and_country"]
    assert _valid(schema, {"asn": 3356})
    assert not _valid(schema, {"asn": 0})
    assert not _valid(schema, {"asn": "3356"})
    assert not _valid(schema, {})


def test_count_nodes_by_asn_and_country_query_groups_and_orders_by_count() -> None:
    executor = RecordingExecutor()
    count_nodes_by_asn_and_country(executor, 3356)
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == (3356,)
    assert "FROM caida_itdk.itdk_node_as" in statement
    assert "JOIN caida_itdk.itdk_node_geolocation" in statement
    assert "COUNT(DISTINCT" in statement.upper() or "COUNT(DISTINCT" in statement
    assert "GROUP BY" in statement
    assert "ORDER BY node_count DESC, country" in statement
    assert [column.name for column in query.columns] == ["country", "node_count"]


# TODO(student): Add at least one test of your own per tool below this line.
