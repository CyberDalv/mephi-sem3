from __future__ import annotations
from pathlib import Path
import pytest
from shell import FileManagerShell
from queued_logger import QueuedLogger

class RecordingLogger:
    def __init__(self):
        self.events = []
    def submit(self, event):
        self.events.append(dict(event))

@pytest.fixture
def shell(workspace) -> FileManagerShell:
    logger = RecordingLogger()
    app = FileManagerShell(logger=logger)
    app.core.workspace = workspace
    app.core.current_dir = workspace
    return app

def test_shell_successful_commands(shell, workspace):
    shell.onecmd("pwd")
    shell.onecmd("ls")
    # Проверяем, что события записались в логгер
    assert len(shell.logger.events) == 2
    assert shell.logger.events[0]["result"] == "OK"

def test_shell_history_limit(shell):
    for i in range(6):
        shell.onecmd("pwd")
    snapshot = shell.history.get_snapshot()
    assert len(snapshot) == 5  # Ограничение N=5
