"""ASGI composition for the official MCP SSE transport and Flask operations."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .app import create_flask_app
from .auth import BearerAuthMiddleware
from .config import Settings
from .data_access import DatabasePool, Repositories
from .mcp_tools import create_mcp_server
from .structured_logging import configure_logging

LOGGER = logging.getLogger(__name__)
MCP_MOUNT_PATH = "/mcp"
MCP_SSE_PATH = "/sse"
MCP_MESSAGE_PATH = "/messages/"


class SseConnectionEndpoint:
    def __init__(self, server: Server[Any, Any], transport: SseServerTransport) -> None:
        self._server = server
        self._transport = transport

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self._transport.connect_sse(scope, receive, send) as streams:
            await self._server.run(
                streams[0], streams[1], self._server.create_initialization_options()
            )


def create_app(settings: Settings | None = None) -> Starlette:
    active_settings = settings or Settings.from_env()
    active_settings.prepare_output_dir()
    configure_logging(active_settings.log_level, secrets=active_settings.log_redaction_values)
    database_pool = DatabasePool.from_settings(active_settings)
    repositories = Repositories.from_settings(active_settings, database_pool)
    flask_app = create_flask_app(active_settings, database_pool, repositories)
    mcp_server = create_mcp_server(repositories)
    sse_transport = SseServerTransport(MCP_MESSAGE_PATH)
    mcp_app = Starlette(
        routes=[
            Route(MCP_SSE_PATH, endpoint=SseConnectionEndpoint(mcp_server, sse_transport)),
            Mount(MCP_MESSAGE_PATH, app=sse_transport.handle_post_message),
        ]
    )
    protected_mcp_app = BearerAuthMiddleware(mcp_app, active_settings.master_key)

    @asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        try:
            database_pool.open()
            LOGGER.info("service initialized", extra={"event": "service_initialized"})
            yield
        finally:
            await anyio.to_thread.run_sync(database_pool.close)
            LOGGER.info("service stopped", extra={"event": "service_stopped"})

    app = Starlette(
        routes=[
            Mount(MCP_MOUNT_PATH, app=protected_mcp_app),
            Mount("/", app=WSGIMiddleware(flask_app)),
        ],
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.state.database_pool = database_pool
    app.state.repositories = repositories
    app.state.mcp_server = mcp_server
    return app
