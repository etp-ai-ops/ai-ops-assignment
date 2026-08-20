"""Executable specifications for student-owned MCP tools.

These tests are expected failures in the distributed starter. Remove the
module-level ``xfail`` marker after implementing the TODO(student) regions,
then add at least one meaningful test of your own to this file.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from itdk_mcp.data_access import CsvResult
from itdk_mcp.data_access.hostnames import HostnameRepository
from itdk_mcp.data_access.links import LinkRepository
from itdk_mcp.data_access.nodes import NodeRepository
from itdk_mcp.data_access.query import Query
from itdk_mcp.mcp_tools import TOOL_DESCRIPTIONS, TOOL_SCHEMAS

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


def test_find_nodes_by_asn_contract_requires_a_positive_integer() -> None:
    schema = TOOL_SCHEMAS["find_nodes_by_asn"]
    assert _valid(schema, {"asn": 64500})
    assert not _valid(schema, {"asn": 64500.5})
    assert not _valid(schema, {"asn": "64500"})
    assert not _valid(schema, {"asn": 0})
    assert not _valid(schema, {"asn": 64500, "raw_sql": "SELECT 1"})


def test_find_nodes_by_asn_query_is_fixed_parameterized_and_ordered() -> None:
    executor = RecordingExecutor()
    NodeRepository(executor).find_nodes_by_asn(64500)
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == (64500,)
    assert "FROM caida_itdk.itdk_node_as" in statement
    assert "WHERE asn = %s" in statement
    assert "ORDER BY node_id" in statement
    assert [column.name for column in query.columns] == ["node_id", "asn", "method"]


def test_geolocation_contract_rejects_bad_country_bounds_and_nonfinite_values() -> None:
    schema = TOOL_SCHEMAS["search_nodes_by_geolocation"]
    assert _valid(schema, {"country": "US", "longitude_min": -120, "longitude_max": -70})
    assert not _valid(schema, {"country": "usa"})
    assert not _valid(schema, {"country": "US", "longitude_min": -181})
    assert not _valid(schema, {"country": "US", "latitude_max": 91})
    assert not _valid(schema, {"country": "US", "longitude_min": float("inf")})


def test_geolocation_query_keeps_country_predicate_and_binds_every_bound() -> None:
    executor = RecordingExecutor()
    NodeRepository(executor).search_nodes_by_geolocation(
        "US", longitude_min=-120.0, longitude_max=-70.0, latitude_min=25.0, latitude_max=50.0
    )
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert statement.index("WHERE country = %s") < statement.index("longitude")
    assert parameters == ("US", -120.0, -120.0, -70.0, -70.0, 25.0, 25.0, 50.0, 50.0)
    assert "ORDER BY country, longitude NULLS FIRST, latitude NULLS FIRST, node_id" in statement
    assert [column.name for column in query.columns] == [
        "node_id", "continent", "country", "region", "city", "latitude", "longitude", "method"
    ]


def test_hostname_contract_requires_exactly_one_well_formed_selector() -> None:
    schema = TOOL_SCHEMAS["lookup_router_hostnames"]
    assert _valid(schema, {"ip": "2001:db8::1"})
    assert _valid(schema, {"hostname_exact": "r1.example.net"})
    assert _valid(schema, {"hostname_prefix": "r1."})
    assert not _valid(schema, {})
    assert not _valid(schema, {"ip": "not-an-ip"})
    assert not _valid(schema, {"ip": "192.0.2.1", "hostname_exact": "r1.example.net"})


def test_hostname_prefix_treats_sql_wildcards_as_literal_characters() -> None:
    executor = RecordingExecutor()
    HostnameRepository(executor).lookup_router_hostnames(hostname_prefix="r%_\\")
    query, parameters = executor.calls[-1]
    assert parameters == (r"r\%\_\\%",)
    assert r"LIKE %s ESCAPE '\'" in _normalized(query)


def test_find_links_for_node_is_a_discoverable_complete_vertical_slice() -> None:
    assert "find_links_for_node" in TOOL_SCHEMAS
    assert "find_links_for_node" in TOOL_DESCRIPTIONS
    schema = TOOL_SCHEMAS["find_links_for_node"]
    assert _valid(schema, {"node_id": "N1"})
    assert not _valid(schema, {"node_id": "N1", "order_by": "random()"})


def test_find_links_for_node_repository_is_fixed_and_stably_ordered() -> None:
    executor = RecordingExecutor()
    LinkRepository(executor).find_links_for_node("N1")
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    assert parameters == ("N1",)
    assert "FROM caida_itdk.itdk_link_endpoints" in statement
    assert "WHERE node_id = %s" in statement
    assert "ORDER BY link_id, endpoint_ordinal" in statement
    assert [column.name for column in query.columns] == [
        "link_id", "endpoint_ordinal", "endpoint_token", "node_id"
    ]


# TODO(student): Add at least one test of your own below this line.
