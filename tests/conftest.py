import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def base_temp(tmp_path, monkeypatch):
    """Base SQLite vide et isolée pour chaque test."""
    from nutrima import db

    monkeypatch.setenv("NUTRIMA_DB", str(tmp_path / "test.db"))
    db.init_db()
    return db
