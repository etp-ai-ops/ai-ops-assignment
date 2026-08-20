from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from mcp import types

from itdk_mcp.auth import BearerAuthMiddleware
from itdk_mcp.config import ConfigurationError, Settings
from itdk_mcp.data_access import Column, CsvResult, CsvResultWriter
from itdk_mcp.data_access.links import LinkRepository
from itdk_mcp.data_access.query import Query
from itdk_mcp.mcp_tools import TOOL_SCHEMAS, execute_tool_call, serialize_csv_result
from itdk_mcp.server import create_app


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[Query, tuple[object, ...]]] = []

    def execute(self, query: Query, parameters: tuple[object, ...]) -> CsvResult:
        self.calls.append((query, parameters))
        return CsvResult(Path("/output/result.csv"), 0, query.columns)


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


def test_starter_discovery_surface_has_four_tools_until_vertical_slice_is_added() -> None:
    assert set(TOOL_SCHEMAS) == {
        "get_link_endpoints",
        "find_nodes_by_asn",
        "search_nodes_by_geolocation",
        "lookup_router_hostnames",
    }


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
