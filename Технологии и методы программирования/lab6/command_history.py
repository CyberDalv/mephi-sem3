from __future__ import annotations
from collections import deque
from typing import Any

class CommandHistory:
    def __init__(self, maxlen: int = 5) -> None:
        self._history: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def append(self, event: dict[str, Any]) -> None:
        self._history.append(event)

    def get_snapshot(self) -> list[dict[str, Any]]:
        return list(self._history)
