from __future__ import annotations
from pathlib import Path
import pytest
from errors import OperationRejectedError

def test_cp_success(core, workspace):
    src = workspace / "inbox" / "source.txt"
    dst_name = "copy.txt"
    core.cmd_cp("inbox/source.txt", dst_name)
    dst = workspace / dst_name
    assert dst.exists()
    assert dst.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")

def test_cp_file_exists_error(core, workspace):
    occupied = workspace / "occupied.txt"
    occupied.write_text("occupied content", encoding="utf-8")
    with pytest.raises(FileExistsError):
        core.cmd_cp("inbox/source.txt", "occupied.txt")

def test_cd_not_a_directory(core, workspace):
    with pytest.raises(NotADirectoryError):
        core.cmd_cd("inbox/source.txt")

def test_rm_directory_rejected(core, workspace):
    with pytest.raises((IsADirectoryError, OperationRejectedError)):
        core.cmd_rm("archive")
