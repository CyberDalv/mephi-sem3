from __future__ import annotations
import sys
from pathlib import Path
from queued_logger import QueuedLogger

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    log_path = Path(sys.argv[1])
    
    logger = QueuedLogger(log_path, maxsize=10)
    logger.start()
    
    # Отправляем три события
    for i in range(3):
        logger.submit({
            "time": "2026-10-23T12:00:00+00:00",
            "command": "test",
            "args": [str(i)],
            "result": "OK",
            "detail": "integration"
        })
        
    logger.close()
    
    # Проверяем файл на диске
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8").splitlines()
        if len(lines) == 3:
            sys.exit(0)
    sys.exit(1)
