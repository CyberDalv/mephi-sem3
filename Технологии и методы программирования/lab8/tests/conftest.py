from __future__ import annotations
from pathlib import Path
import pytest
from file_ops import FileManagerCore

@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / "inbox").mkdir(parents=True)
    (root / "archive").mkdir()
    (root / "inbox" / "source.txt").write_text(
        "Учебные данные\n", encoding="utf-8"
    )
    return root

@pytest.fixture
def core(workspace: Path) -> FileManagerCore:
    return FileManagerCore(workspace)
