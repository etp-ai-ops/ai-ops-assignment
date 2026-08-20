"""Flask application factory for unauthenticated operational endpoints."""

from __future__ import annotations

import logging
import os
from typing import Any

from flask import Flask, jsonify

from .config import Settings
from .data_access import DatabasePool, Repositories

LOGGER = logging.getLogger(__name__)


def create_flask_app(
    settings: Settings, database_pool: DatabasePool, repositories: Repositories
) -> Flask:
    app = Flask(__name__)
    app.config["ITDK_SETTINGS"] = settings
    app.config["ITDK_DATABASE_POOL"] = database_pool
    app.config["ITDK_REPOSITORIES"] = repositories

    @app.get("/healthz")
    def healthz() -> tuple[Any, int]:
        return jsonify(status="ok"), 200

    @app.get("/readyz")
    def readyz() -> tuple[Any, int]:
        if not settings.output_dir.is_dir() or not os.access(settings.output_dir, os.W_OK):
            return jsonify(status="not_ready"), 503
        try:
            database_pool.check()
        except Exception:
            LOGGER.warning("database readiness check failed", extra={"event": "database_not_ready"})
            return jsonify(status="not_ready"), 503
        return jsonify(status="ready"), 200

    return app
