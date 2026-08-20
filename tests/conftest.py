from __future__ import annotations

from pathlib import Path

import pytest

from itdk_mcp.config import Settings

TEST_MASTER_KEY = "test-master-key-that-is-at-least-32-bytes"
TEST_DATABASE_URL = "postgresql://test_user:test_password@127.0.0.1/test_db"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        master_key=TEST_MASTER_KEY,
        database_url=TEST_DATABASE_URL,
        output_dir=tmp_path,
    )
