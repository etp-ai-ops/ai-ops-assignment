"""ASGI module used by a production-style server command."""

from .server import create_app

app = create_app()
