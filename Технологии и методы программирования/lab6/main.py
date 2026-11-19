from __future__ import annotations
import sys
from queued_logger import QueuedLogger
from shell import FileManagerShell

def main() -> int:
    logger = QueuedLogger("command_log.jsonl", maxsize=20)
    logger.start()

    app = FileManagerShell(logger=logger)
    exit_code = 0  # Переменная для хранения кода возврата
    
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print("\nЗавершение работы.")
    finally:
        logger.close()
        if logger.failures:
            print(f"Внимание: зафиксировано ошибок записи в лог: {len(logger.failures)}")
            exit_code = 1  # Меняем код возврата, но не делаем return внутри finally!
            
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
