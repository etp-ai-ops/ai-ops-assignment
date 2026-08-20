"""Verify health, authenticated discovery, and the completed warm-up tool."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.request

from .common import open_session, preview_csv, structured_metadata


async def main() -> None:
    port = os.environ.get("MCP_PORT", "8000")
    snapshot_id = os.environ.get("ITDK_SNAPSHOT_ID", "unconfigured")
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=3) as response:
        health = json.load(response)
    if health.get("status") != "ok":
        raise RuntimeError(f"Unexpected health response: {health!r}")

    async with open_session() as session:
        discovered = await session.list_tools()
        names = [tool.name for tool in discovered.tools]
        required = {
            "get_link_endpoints",
            "find_nodes_by_asn",
            "search_nodes_by_geolocation",
            "lookup_router_hostnames",
        }
        allowed = required | {
            "find_links_for_node",
            "find_peer_asns_for_node",
            "find_hostnames_for_asn",
        }
        if not required.issubset(names) or not set(names).issubset(allowed):
            raise RuntimeError(f"Unexpected tool set: {names!r}")
        result = await session.call_tool("get_link_endpoints", {"link_id": "L1"})

    metadata = structured_metadata(result)
    if metadata.get("row_count") != 2:
        raise RuntimeError(f"Expected two L1 endpoints, received: {metadata!r}")
    print("health: ok")
    print("snapshot:", snapshot_id)
    print("snapshot:", os.environ.get("ITDK_SNAPSHOT_ID", "nids-itdk-mcp-synthetic-v1"))
    print("tools:", ", ".join(sorted(names)))
    print("get_link_endpoints metadata:", json.dumps(metadata, sort_keys=True))
    print("CSV preview:", preview_csv(metadata, row_limit=2))


if __name__ == "__main__":
    asyncio.run(main())
