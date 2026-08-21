from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from mcp import types

from itdk_mcp.auth import BearerAuthMiddleware
from itdk_mcp.config import ConfigurationError, Settings
from itdk_mcp.data_access import Column, CsvResult, CsvResultWriter
from itdk_mcp.data_access.hostnames import HostnameRepository
from itdk_mcp.data_access.links import LinkRepository
from itdk_mcp.data_access.nodes import NodeRepository
from itdk_mcp.data_access.query import Query
from itdk_mcp.mcp_tools import MAX_ASN, TOOL_SCHEMAS, execute_tool_call, serialize_csv_result
from itdk_mcp.server import create_app


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


def _fake_repositories(**overrides: object) -> SimpleNamespace:
    base = {
        "links": SimpleNamespace(),
        "nodes": SimpleNamespace(),
        "hostnames": SimpleNamespace(),
        "executor": SimpleNamespace(),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_get_link_endpoints_is_a_complete_parameterized_example() -> None:
    executor = RecordingExecutor()
    result = LinkRepository(executor).get_link_endpoints("link'; DROP TABLE x; --")
    query, parameters = executor.calls[-1]
    statement = " ".join(query.statement.as_string().split())
    assert statement.startswith("SELECT link_id, endpoint_ordinal, endpoint_token, node_id")
    assert "WHERE link_id = %s" in statement
    assert "ORDER BY endpoint_ordinal" in statement
    assert parameters == ("link'; DROP TABLE x; --",)
    assert parameters[0] not in statement
    assert [column.name for column in result.columns] == [
        "link_id",
        "endpoint_ordinal",
        "endpoint_token",
        "node_id",
    ]


async def test_get_link_endpoints_dispatches_and_serializes_metadata(tmp_path: Path) -> None:
    expected = CsvResult(tmp_path / "result.csv", 2, (Column("link_id", "string"),))

    class Links:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def get_link_endpoints(self, link_id: str) -> CsvResult:
            self.calls.append(link_id)
            return expected

    links = Links()
    repositories = SimpleNamespace(
        links=links,
        nodes=SimpleNamespace(),
        hostnames=SimpleNamespace(),
    )
    response = await execute_tool_call(repositories, "get_link_endpoints", {"link_id": "L1"})
    assert response == serialize_csv_result(expected)
    assert links.calls == ["L1"]


async def test_worked_tool_rejects_extra_input_before_dispatch() -> None:
    repositories = SimpleNamespace(
        links=SimpleNamespace(get_link_endpoints=lambda _: pytest.fail("must not dispatch")),
        nodes=SimpleNamespace(),
        hostnames=SimpleNamespace(),
    )
    response = await execute_tool_call(
        repositories, "get_link_endpoints", {"link_id": "L1", "raw_sql": "SELECT 1"}
    )
    assert isinstance(response, types.CallToolResult)
    assert response.isError is True
    assert response.content[0].text == "INVALID_ARGUMENT"


def test_unknown_tool_returns_safe_error_schema_is_not_open() -> None:
    assert "raw_sql" not in TOOL_SCHEMAS


def test_discovery_surface_always_has_the_four_complete_tools() -> None:
    """The four provided tools stay registered whether or not student_tools.py
    has been filled in yet -- this checks a subset, not an exact set, so it
    holds in both the starter state and after the three new tools are added."""
    assert {
        "get_link_endpoints",
        "find_nodes_by_asn",
        "search_nodes_by_geolocation",
        "lookup_router_hostnames",
    }.issubset(TOOL_SCHEMAS)


# ---------------------------------------------------------------------------
# find_nodes_by_asn: complete, restrictive schema + fixed repository query.
# ---------------------------------------------------------------------------


def test_find_nodes_by_asn_contract_requires_a_positive_integer() -> None:
    schema = TOOL_SCHEMAS["find_nodes_by_asn"]
    assert _valid(schema, {"asn": 1})
    assert _valid(schema, {"asn": 64500})
    assert _valid(schema, {"asn": MAX_ASN})
    assert not _valid(schema, {"asn": 64500.5})
    assert not _valid(schema, {"asn": "64500"})
    assert not _valid(schema, {"asn": 0})
    assert not _valid(schema, {"asn": -1})
    assert not _valid(schema, {"asn": MAX_ASN + 1})
    assert not _valid(schema, {})
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


async def test_find_nodes_by_asn_dispatches_and_rejects_extra_input() -> None:
    class Nodes:
        def __init__(self) -> None:
            self.calls: list[int] = []

        def find_nodes_by_asn(self, asn: int) -> CsvResult:
            self.calls.append(asn)
            return CsvResult(Path("/output/result.csv"), 1, ())

    nodes = Nodes()
    repositories = _fake_repositories(nodes=nodes)
    response = await execute_tool_call(repositories, "find_nodes_by_asn", {"asn": 64500})
    assert response == serialize_csv_result(CsvResult(Path("/output/result.csv"), 1, ()))
    assert nodes.calls == [64500]

    rejected = await execute_tool_call(repositories, "find_nodes_by_asn", {"asn": 0})
    assert isinstance(rejected, types.CallToolResult)
    assert rejected.isError is True


# ---------------------------------------------------------------------------
# search_nodes_by_geolocation: complete schema + application-level bounds.
# ---------------------------------------------------------------------------


def test_geolocation_contract_rejects_bad_country_bounds_and_extra_properties() -> None:
    schema = TOOL_SCHEMAS["search_nodes_by_geolocation"]
    assert _valid(schema, {"country": "US"})
    assert _valid(schema, {"country": "US", "longitude_min": -120, "longitude_max": -70})
    assert not _valid(schema, {})
    assert not _valid(schema, {"country": "usa"})
    assert not _valid(schema, {"country": "us"})
    assert not _valid(schema, {"country": "US", "longitude_min": -181})
    assert not _valid(schema, {"country": "US", "longitude_max": 181})
    assert not _valid(schema, {"country": "US", "latitude_min": -91})
    assert not _valid(schema, {"country": "US", "latitude_max": 91})
    assert not _valid(schema, {"country": "US", "longitude_min": float("inf")})
    assert not _valid(schema, {"country": "US", "order_by": "random()"})


async def test_geolocation_application_validation_rejects_nonfinite_and_inverted_bounds() -> None:
    repositories = _fake_repositories(
        nodes=SimpleNamespace(
            search_nodes_by_geolocation=lambda *a, **k: pytest.fail("must not dispatch")
        )
    )
    nan_response = await execute_tool_call(
        repositories,
        "search_nodes_by_geolocation",
        {"country": "US", "longitude_min": float("nan")},
    )
    assert isinstance(nan_response, types.CallToolResult)
    assert nan_response.isError is True

    inverted_response = await execute_tool_call(
        repositories,
        "search_nodes_by_geolocation",
        {"country": "US", "longitude_min": -70.0, "longitude_max": -120.0},
    )
    assert isinstance(inverted_response, types.CallToolResult)
    assert inverted_response.isError is True


def test_geolocation_query_keeps_country_predicate_and_binds_every_bound() -> None:
    executor = RecordingExecutor()
    NodeRepository(executor).search_nodes_by_geolocation(
        "US", longitude_min=-120.0, longitude_max=-70.0, latitude_min=25.0, latitude_max=50.0
    )
    query, parameters = executor.calls[-1]
    statement = _normalized(query)
    where_index = statement.index("WHERE country = %s")
    assert where_index < statement.index("longitude", where_index)
    assert parameters == ("US", -120.0, -120.0, -70.0, -70.0, 25.0, 25.0, 50.0, 50.0)
    assert "ORDER BY country, longitude NULLS FIRST, latitude NULLS FIRST, node_id" in statement
    assert [column.name for column in query.columns] == [
        "node_id", "continent", "country", "region", "city", "latitude", "longitude", "method"
    ]


def test_geolocation_query_binds_nulls_for_omitted_bounds() -> None:
    executor = RecordingExecutor()
    NodeRepository(executor).search_nodes_by_geolocation("DE")
    _, parameters = executor.calls[-1]
    assert parameters == ("DE", None, None, None, None, None, None, None, None)


# ---------------------------------------------------------------------------
# lookup_router_hostnames: complete mutually-exclusive selector + escaping.
# ---------------------------------------------------------------------------


def test_hostname_contract_requires_exactly_one_well_formed_selector() -> None:
    schema = TOOL_SCHEMAS["lookup_router_hostnames"]
    assert _valid(schema, {"ip": "2001:db8::1"})
    assert _valid(schema, {"ip": "192.0.2.1"})
    assert _valid(schema, {"hostname_exact": "r1.example.net"})
    assert _valid(schema, {"hostname_prefix": "r1."})
    assert not _valid(schema, {})
    assert not _valid(schema, {"ip": "192.0.2.1", "hostname_exact": "r1.example.net"})
    assert not _valid(schema, {"ip": "192.0.2.1", "hostname_prefix": "r1."})
    assert not _valid(schema, {"hostname_exact": "r1.example.net", "hostname_prefix": "r1."})
    assert not _valid(
        schema,
        {"ip": "192.0.2.1", "hostname_exact": "r1.example.net", "hostname_prefix": "r1."},
    )
    assert not _valid(schema, {"hostname_prefix": "ab"})
    assert not _valid(schema, {"ip": "192.0.2.1", "raw_sql": "SELECT 1"})


async def test_hostname_application_validation_parses_ipv4_and_ipv6_only() -> None:
    repositories = _fake_repositories(
        hostnames=SimpleNamespace(
            lookup_router_hostnames=lambda **k: pytest.fail("must not dispatch")
        )
    )
    response = await execute_tool_call(
        repositories, "lookup_router_hostnames", {"ip": "not-an-ip"}
    )
    assert isinstance(response, types.CallToolResult)
    assert response.isError is True


async def test_hostname_dispatches_valid_ipv4_and_ipv6_selectors() -> None:
    class Hostnames:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def lookup_router_hostnames(self, **kwargs: object) -> CsvResult:
            self.calls.append(kwargs)
            return CsvResult(Path("/output/result.csv"), 0, ())

    hostnames = Hostnames()
    repositories = _fake_repositories(hostnames=hostnames)
    for ip in ("192.0.2.1", "2001:db8::1"):
        await execute_tool_call(repositories, "lookup_router_hostnames", {"ip": ip})
    assert [call["ip"] for call in hostnames.calls] == ["192.0.2.1", "2001:db8::1"]


def test_hostname_prefix_treats_sql_wildcards_as_literal_characters() -> None:
    executor = RecordingExecutor()
    HostnameRepository(executor).lookup_router_hostnames(hostname_prefix="r%_\\")
    query, parameters = executor.calls[-1]
    assert parameters == (r"r\%\_\\%",)
    assert r"LIKE %s ESCAPE '\'" in _normalized(query)


def test_hostname_lookup_by_ip_and_exact_name_use_documented_projections_and_order() -> None:
    executor = RecordingExecutor()
    HostnameRepository(executor).lookup_router_hostnames(ip="192.0.2.1")
    query, parameters = executor.calls[-1]
    assert parameters == ("192.0.2.1",)
    assert "WHERE ip = %s" in _normalized(query)
    assert "ORDER BY ip, hostname NULLS FIRST" in _normalized(query)
    assert [column.name for column in query.columns] == ["ip", "hostname"]

    executor2 = RecordingExecutor()
    HostnameRepository(executor2).lookup_router_hostnames(hostname_exact="r1.example.net")
    query2, parameters2 = executor2.calls[-1]
    assert parameters2 == ("r1.example.net",)
    assert "WHERE hostname = %s" in _normalized(query2)
    assert "ORDER BY hostname, ip" in _normalized(query2)


def test_hostname_repository_rejects_zero_or_multiple_selectors_directly() -> None:
    executor = RecordingExecutor()
    repository = HostnameRepository(executor)
    with pytest.raises(ValueError):
        repository.lookup_router_hostnames()
    with pytest.raises(ValueError):
        repository.lookup_router_hostnames(ip="192.0.2.1", hostname_exact="r1.example.net")
    assert executor.calls == []


def test_csv_writer_publishes_typed_deterministic_content(tmp_path: Path) -> None:
    result = CsvResultWriter(tmp_path).write(
        filename_prefix="Unsafe Prefix!?",
        columns=(Column("name", "string"), Column("asn", "int64")),
        rows=[(r"r\one", 64500), (None, 64501)],
    )
    assert result.file_path.parent == tmp_path
    assert result.file_path.name.startswith("unsafe_prefix_")
    assert result.row_count == 2
    with result.file_path.open(newline="", encoding="utf-8") as source:
        assert list(csv.reader(source)) == [
            ["name", "asn"],
            [r"r\\one", "64500"],
            [r"\N", "64501"],
        ]


def test_settings_validate_secrets_database_and_output_path(tmp_path: Path) -> None:
    settings = Settings.from_env(
        {
            "MCP_MASTER_KEY": "x" * 32,
            "DATABASE_URL": "postgresql://reader:secret@db/itdk",
            "OUTPUT_DIR": str(tmp_path / "outputs"),
        }
    )
    settings.prepare_output_dir()
    assert settings.output_dir.is_dir()
    with pytest.raises(ConfigurationError):
        Settings.from_env({"MCP_MASTER_KEY": "short", "DATABASE_URL": "sqlite:///x"})


def test_create_app_keeps_health_outside_authenticated_mcp(settings: Settings) -> None:
    app = create_app(settings)
    assert [route.path for route in app.routes] == ["/mcp", ""]
    assert app.state.settings is settings


async def test_bearer_auth_rejects_missing_credentials() -> None:
    delegated = False

    async def downstream(scope: Any, receive: Any, send: Any) -> None:
        nonlocal delegated
        delegated = True

    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    middleware = BearerAuthMiddleware(downstream, "x" * 32)
    await middleware({"type": "http", "headers": []}, receive, send)
    assert delegated is False
    assert messages[0]["status"] == 401
