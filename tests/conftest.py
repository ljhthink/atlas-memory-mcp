from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from atlas_memory.config import Config
from atlas_memory.storage.database import Database


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        yield Path(d)


@pytest.fixture
def config(temp_dir: Path) -> Config:
    return Config(
        memory_db_path=str(temp_dir / "memory.db"),
        chroma_path=str(temp_dir / "chroma"),
        project_root=str(temp_dir / "project"),
    )


@pytest.fixture
def db(config: Config) -> Database:
    _db = Database(config)
    yield _db
    _db.close()
