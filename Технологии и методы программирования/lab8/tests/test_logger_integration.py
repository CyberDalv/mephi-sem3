from __future__ import annotations
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.mark.integration
def test_queued_logger_integration(tmp_path: Path):
    log_file = tmp_path / "real_command_log.jsonl"
    
    cmd = [sys.executable, "-m", "tests.helpers.logger_probe", str(log_file)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    assert res.returncode == 0, f"Stderr: {res.stderr}"
    assert log_file.exists()
    
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
