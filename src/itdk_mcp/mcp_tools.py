"""MCP schemas, validation, dispatch, and safe error mapping.

Only ``get_link_endpoints`` is complete in the starter. Search for
``TODO(student)`` to find the intentionally narrow learning surface.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import Any, Final, cast

import anyio
from jsonschema import Draft202012Validator, FormatChecker
from mcp import types
from mcp.server.lowlevel import Server

from .data_access import CsvResult, Repositories

LOGGER = logging.getLogger(__name__)
MAX_IDENTIFIER_LENGTH: Final = 255
MAX_ASN: Final = 9_223_372_036_854_775_807

IDENTIFIER_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "minLength": 1,
    "maxLength": MAX_IDENTIFIER_LENGTH,
    "pattern": r"^(?=.*\S)[^\x00-\x1f\x7f]+$",
}
OUTPUT_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["file_path", "row_count", "columns"],
    "properties": {
        "file_path": {"type": "string"},
        "row_count": {"type": "integer", "minimum": 0},
        "columns": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "type"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["string", "inet", "int32", "int64", "float64"],
                    },
                },
            },
        },
    },
}


def _object_schema(
    properties: dict[str, Any],
    *,
    required: list[str] | None = None,
    one_of: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        schema["required"] = required
    if one_of:
        schema["oneOf"] = one_of
    return schema


TOOL_SCHEMAS: Final[dict[str, dict[str, Any]]] = {
    "get_link_endpoints": _object_schema({"link_id": IDENTIFIER_SCHEMA}, required=["link_id"]),
    # TODO(student): Replace the three intentionally incomplete contracts below
    # with restrictive schemas. Add find_links_for_node as the fourth task's
    # complete vertical slice.
    "find_nodes_by_asn": _object_schema({"asn": {"type": "number"}}, required=["asn"]),
    "search_nodes_by_geolocation": _object_schema(
        {
            "country": {"type": "string"},
            "longitude_min": {"type": "number"},
            "longitude_max": {"type": "number"},
            "latitude_min": {"type": "number"},
            "latitude_max": {"type": "number"},
        },
        required=["country"],
    ),
    "lookup_router_hostnames": _object_schema(
        {
            "ip": {"type": "string"},
            "hostname_exact": {"type": "string"},
            "hostname_prefix": {"type": "string"},
        }
    ),
}

TOOL_DESCRIPTIONS: Final[dict[str, str]] = {
    "get_link_endpoints": "Write every endpoint for one link to CSV.",
    "find_nodes_by_asn": "Write nodes assigned to one ASN to CSV.",
    "search_nodes_by_geolocation": "Write nodes in one country and optional bounds to CSV.",
    "lookup_router_hostnames": (
        "Write router hostnames selected by exactly one IP, exact name, or prefix to CSV."
    ),
    # TODO(student): Add find_links_for_node with a precise description.
}


class SafeToolError(Exception):
    """An intentionally content-free stable MCP tool error."""


def create_mcp_server(repositories: Repositories) -> Server[Any, Any]:
    server: Server[Any, Any] = Server(
        "itdk-mcp",
        version="0.1.0",
        instructions="Read-only deterministic access to CAIDA ITDK data via CSV metadata.",
    )

    @server.list_tools()  # type: ignore[no-untyped-call,untyped-decorator]
    async def list_tools() -> list[types.Tool]:
        annotations = types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
        return [
            types.Tool(
                name=name,
                description=TOOL_DESCRIPTIONS[name],
                inputSchema=schema,
                outputSchema=OUTPUT_SCHEMA,
                annotations=annotations,
            )
            for name, schema in TOOL_SCHEMAS.items()
        ]

    @server.call_tool(validate_input=False)  # type: ignore[untyped-decorator]
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> dict[str, Any] | types.CallToolResult:
        return await execute_tool_call(repositories, name, arguments)

    return server


async def execute_tool_call(
    repositories: Repositories, name: str, arguments: dict[str, Any]
) -> dict[str, Any] | types.CallToolResult:
    try:
        _validate_input(name, arguments)
        result = await _dispatch(repositories, name, arguments)
        return serialize_csv_result(result)
    except SafeToolError:
        LOGGER.warning(
            "tool input rejected",
            extra={
                "event": "tool_error",
                "context": {
                    "code": "INVALID_ARGUMENT",
                    "tool": name if name in TOOL_SCHEMAS else "unknown",
                },
            },
        )
        return _error_result("INVALID_ARGUMENT")
    except Exception as exc:
        LOGGER.error(
            "tool execution failed",
            extra={
                "event": "tool_error",
                "context": {
                    "code": "INTERNAL_ERROR",
                    "tool": name if name in TOOL_SCHEMAS else "unknown",
                    "category": type(exc).__name__,
                },
            },
        )
        return _error_result("INTERNAL_ERROR")


def serialize_csv_result(result: CsvResult) -> dict[str, Any]:
    return {
        "file_path": str(result.file_path),
        "row_count": result.row_count,
        "columns": [{"name": column.name, "type": column.type} for column in result.columns],
    }


def _error_result(code: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=code)], isError=True)


def _validate_input(name: str, arguments: dict[str, Any]) -> None:
    schema = TOOL_SCHEMAS.get(name)
    if schema is None:
        raise SafeToolError("INVALID_ARGUMENT")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    if next(validator.iter_errors(arguments), None) is not None:
        raise SafeToolError("INVALID_ARGUMENT")

    # TODO(student): Add finite/range/cross-field checks for geolocation and
    # standards-based IPv4/IPv6 parsing for lookup_router_hostnames.


async def _dispatch(
    repositories: Repositories, name: str, arguments: dict[str, Any]
) -> CsvResult:
    operation: Callable[[], CsvResult]
    if name == "get_link_endpoints":
        operation = partial(repositories.links.get_link_endpoints, cast(str, arguments["link_id"]))
    elif name == "find_nodes_by_asn":
        operation = partial(repositories.nodes.find_nodes_by_asn, cast(int, arguments["asn"]))
    elif name == "search_nodes_by_geolocation":
        operation = partial(
            repositories.nodes.search_nodes_by_geolocation,
            cast(str, arguments["country"]),
            longitude_min=cast(float | None, arguments.get("longitude_min")),
            longitude_max=cast(float | None, arguments.get("longitude_max")),
            latitude_min=cast(float | None, arguments.get("latitude_min")),
            latitude_max=cast(float | None, arguments.get("latitude_max")),
        )
    elif name == "lookup_router_hostnames":
        operation = partial(
            repositories.hostnames.lookup_router_hostnames,
            ip=cast(str | None, arguments.get("ip")),
            hostname_exact=cast(str | None, arguments.get("hostname_exact")),
            hostname_prefix=cast(str | None, arguments.get("hostname_prefix")),
        )
    # TODO(student): Dispatch find_links_for_node through repositories.links.
    else:
        raise SafeToolError("INVALID_ARGUMENT")
    return await anyio.to_thread.run_sync(operation)
