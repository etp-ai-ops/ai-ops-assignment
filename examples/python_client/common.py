"""Shared MCP-only helpers for the assignment examples."""

from __future__ import annotations

import csv
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp/sse"
DEFAULT_SERVER_OUTPUT_DIR = "/app/outputs"


def required_master_key() -> str:
    """Return the bearer key without printing or persisting it."""
    key = os.environ.get("MCP_MASTER_KEY", "")
    if not key:
        raise RuntimeError(
            "MCP_MASTER_KEY is not exported. Source itdk_mcp_credentials.env before running "
            "the client."
        )
    return key


@asynccontextmanager
async def open_session() -> AsyncIterator[ClientSession]:
    """Open and initialize one authenticated legacy HTTP+SSE session."""
    headers = {"Authorization": f"Bearer {required_master_key()}"}
    async with (
        sse_client(os.environ.get("ITDK_MCP_URL", DEFAULT_MCP_URL), headers=headers) as streams,
        ClientSession(*streams) as session,
    ):
        await session.initialize()
        yield session


def structured_metadata(result: Any) -> dict[str, Any]:
    """Extract successful CSV metadata from an MCP SDK result."""
    payload = result.model_dump(mode="json", by_alias=True)
    if payload.get("isError"):
        raise RuntimeError(f"MCP tool returned an error: {payload.get('content')!r}")
    metadata = payload.get("structuredContent")
    if not isinstance(metadata, dict):
        raise RuntimeError("MCP tool returned no structuredContent metadata")
    return metadata


def local_output_path(server_file_path: str) -> Path:
    """Safely map an /app/outputs result to the host bind mount."""
    server_root = Path(os.environ.get("ITDK_SERVER_OUTPUT_DIR", DEFAULT_SERVER_OUTPUT_DIR))
    relative = Path(server_file_path).relative_to(server_root)
    local_root = Path(os.environ.get("ITDK_OUTPUT_DIR", "./outputs"))
    return local_root / relative


def preview_csv(metadata: dict[str, Any], row_limit: int = 5) -> list[list[str]]:
    """Read only the MCP-produced CSV and return its header plus a short preview."""
    path = local_output_path(str(metadata["file_path"]))
    with path.open(encoding="utf-8", newline="") as source:
        rows = []
        for index, row in enumerate(csv.reader(source)):
            rows.append(row)
            if index >= row_limit:
                break
    return rows
