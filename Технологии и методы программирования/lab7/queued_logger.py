from __future__ import annotations
import queue
import threading
from typing import Any
from command_log import CommandLogger

STOP = object()

class QueuedLogger:
    def __init__(self, log_path: str = "command_log.jsonl", maxsize: int = 20) -> None:
        self.queue: queue.Queue[Any] = queue.Queue(maxsize=maxsize)
        self.sink = CommandLogger(log_path)
        self.failures: list[str] = []
        self.thread = threading.Thread(target=self._consume_loop, daemon=False)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self.thread.start()
            self._started = True

    def submit(self, event: dict[str, Any]) -> None:
        self.queue.put(event)

    def _consume_loop(self) -> None:
        while True:
            item = self.queue.get()
            try:
                if item is STOP:
                    return
                try:
                    self.sink.append(
                        command=item["command"],
                        args=item["args"],
                        result=item["result"],
                        detail=item["detail"]
                    )
                except OSError as exc:
                    self.failures.append(str(exc))
            finally:
                self.queue.task_done()

    def close(self) -> None:
        if self._started:
            self.queue.put(STOP)
            self.queue.join()
            self.thread.join()
