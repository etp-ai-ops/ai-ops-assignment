"""MCP schemas, validation, dispatch, and safe error mapping.

``get_link_endpoints``, ``find_nodes_by_asn``, ``search_nodes_by_geolocation``,
and ``lookup_router_hostnames`` are complete, restrictive, fully-worked tool
contracts. Nothing in this file is student work: the three remaining tools
(``get_node_geolocation``, ``find_router_links_between_asns``, and
``count_nodes_by_asn_and_country``) are declared, implemented, and dispatched
entirely from ``student_tools.py`` -- search ``TODO(student)`` there. Their
schemas and descriptions are merged into the registries below automatically,
and any call naming one of them is routed to ``student_tools.dispatch``.
"""

from __future__ import annotations

import ipaddress
import logging
import math
from collections.abc import Callable
from functools import partial
from typing import Any, Final, cast

import anyio
from jsonschema import Draft202012Validator, FormatChecker
from mcp import types
from mcp.server.lowlevel import Server

from . import student_tools
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
COUNTRY_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "pattern": r"^[A-Z]{2}$",
}
LONGITUDE_SCHEMA: Final[dict[str, Any]] = {
    "type": "number",
    "minimum": -180,
    "maximum": 180,
}
LATITUDE_SCHEMA: Final[dict[str, Any]] = {
    "type": "number",
    "minimum": -90,
    "maximum": 90,
}
IP_SELECTOR_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "minLength": 1,
    "maxLength": 45,
}
HOSTNAME_EXACT_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "minLength": 1,
    "maxLength": MAX_IDENTIFIER_LENGTH,
    "pattern": r"^(?=.*\S)[^\x00-\x1f\x7f]+$",
}
HOSTNAME_PREFIX_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "minLength": 3,
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
    "find_nodes_by_asn": _object_schema(
        {"asn": {"type": "integer", "exclusiveMinimum": 0, "maximum": MAX_ASN}},
        required=["asn"],
    ),
    "search_nodes_by_geolocation": _object_schema(
        {
            "country": COUNTRY_SCHEMA,
            "longitude_min": LONGITUDE_SCHEMA,
            "longitude_max": LONGITUDE_SCHEMA,
            "latitude_min": LATITUDE_SCHEMA,
            "latitude_max": LATITUDE_SCHEMA,
        },
        required=["country"],
    ),
    "lookup_router_hostnames": _object_schema(
        {
            "ip": IP_SELECTOR_SCHEMA,
            "hostname_exact": HOSTNAME_EXACT_SCHEMA,
            "hostname_prefix": HOSTNAME_PREFIX_SCHEMA,
        },
        one_of=[
            {"required": ["ip"], "properties": {"hostname_exact": False, "hostname_prefix": False}},
            {"required": ["hostname_exact"], "properties": {"ip": False, "hostname_prefix": False}},
            {"required": ["hostname_prefix"], "properties": {"ip": False, "hostname_exact": False}},
        ],
    ),
    # The three student tools are declared in student_tools.py and merged in
    # below; nothing needs to be added here.
    **student_tools.STUDENT_TOOL_SCHEMAS,
}

TOOL_DESCRIPTIONS: Final[dict[str, str]] = {
    "get_link_endpoints": "Write every endpoint for one link to CSV.",
    "find_nodes_by_asn": "Write nodes assigned to one ASN to CSV.",
    "search_nodes_by_geolocation": "Write nodes in one country and optional bounds to CSV.",
    "lookup_router_hostnames": (
        "Write router hostnames selected by exactly one IP, exact name, or prefix to CSV."
    ),
    **student_tools.STUDENT_TOOL_DESCRIPTIONS,
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

    if name == "search_nodes_by_geolocation":
        _validate_geolocation_bounds(arguments)
    elif name == "lookup_router_hostnames":
        _validate_ip_selector(arguments)


def _validate_geolocation_bounds(arguments: dict[str, Any]) -> None:
    for key in ("longitude_min", "longitude_max", "latitude_min", "latitude_max"):
        value = arguments.get(key)
        if value is not None and not math.isfinite(value):
            raise SafeToolError("INVALID_ARGUMENT")
    longitude_min, longitude_max = arguments.get("longitude_min"), arguments.get("longitude_max")
    if longitude_min is not None and longitude_max is not None and longitude_min > longitude_max:
        raise SafeToolError("INVALID_ARGUMENT")
    latitude_min, latitude_max = arguments.get("latitude_min"), arguments.get("latitude_max")
    if latitude_min is not None and latitude_max is not None and latitude_min > latitude_max:
        raise SafeToolError("INVALID_ARGUMENT")


def _validate_ip_selector(arguments: dict[str, Any]) -> None:
    ip = arguments.get("ip")
    if ip is None:
        return
    try:
        ipaddress.ip_address(ip)
    except ValueError as exc:
        raise SafeToolError("INVALID_ARGUMENT") from exc


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
    elif name in student_tools.STUDENT_TOOL_SCHEMAS:
        # Every student tool is routed through one branch; student_tools.py
        # owns the schema, the description, and the fixed query.
        student_result = await anyio.to_thread.run_sync(
            partial(student_tools.dispatch, repositories.executor, name, arguments)
        )
        if student_result is None:
            raise SafeToolError("INVALID_ARGUMENT")
        return student_result
    else:
        raise SafeToolError("INVALID_ARGUMENT")
    return await anyio.to_thread.run_sync(operation)
