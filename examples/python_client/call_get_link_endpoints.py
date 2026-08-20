"""Call the completed get_link_endpoints warm-up tool for synthetic link L1."""

from __future__ import annotations

import asyncio
import json

from .common import open_session, preview_csv, structured_metadata


async def main() -> None:
    async with open_session() as session:
        result = await session.call_tool("get_link_endpoints", {"link_id": "L1"})
    metadata = structured_metadata(result)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    for row in preview_csv(metadata):
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
