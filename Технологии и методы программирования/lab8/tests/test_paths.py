from __future__ import annotations
from pathlib import Path
import pytest
from errors import WorkspaceViolationError

@pytest.mark.parametrize(
    "raw_path, expected_sub",
    [
        ("/", Path("workspace")),
        ("inbox/source.txt", Path("workspace/inbox/source.txt")),
        ("/inbox/source.txt", Path("workspace/inbox/source.txt")),
    ],
    ids=["root", "relative_file", "absolute_style_file"]
)
def test_path_resolution_valid(core, workspace, raw_path, expected_sub):
    resolved = core.resolve_path(raw_path, must_exist=False)
    assert resolved.is_relative_to(workspace.parent)

@pytest.mark.parametrize(
    "bad_path",
    [
        "../outside.txt",
        "..\\outside.txt",
        "C:/temp/file.txt" if Path("C:/").exists() else "/etc/passwd",
    ],
    ids=["parent_escape", "backslash_escape", "absolute_system"]
)
def test_path_resolution_violations(core, workspace, bad_path):
    with pytest.raises(WorkspaceViolationError):
        core.resolve_path(bad_path, must_exist=False)

def test_path_must_exist(core, workspace):
    non_existent = "missing.txt"
    # Допустимый будущий путь при must_exist=False
    res_false = core.resolve_path(non_existent, must_exist=False)
    assert not res_false.exists()

    # FileNotFoundError при must_exist=True
    with pytest.raises(FileNotFoundError):
        core.resolve_path(non_existent, must_exist=True)
