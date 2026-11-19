from __future__ import annotations
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

class CommandLogger:
    def __init__(self, log_path: Path | str = "command_log.jsonl") -> None:
        self.log_path = Path(log_path)
        self.semaphore = threading.Semaphore(1)

    def append(self, command: str, args: list[str] | None, result: str, detail: str) -> None:
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "command": command.lower().strip(),
            "args": args,
            "result": result,  # OK, ERROR, CANCELLED
            "detail": detail
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        
        with self.semaphore:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception as e:
                print(f"ERROR logging: {e}")
