from __future__ import annotations
import sys
from queued_logger import QueuedLogger
from shell import FileManagerShell

def main() -> int:
    logger = QueuedLogger("command_log.jsonl", maxsize=20)
    logger.start()

    app = FileManagerShell(logger=logger)
    exit_code = 0
    
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print("\nЗавершение работы.")
    except Exception as exc:
        # Для неожиданных ошибок в главном потоке фиксируем событие ошибки в лог
        print(f"\nНеожиданная ошибка в главном потоке: {exc}", file=sys.stderr)
        exit_code = 1
        raise
    finally:
        # Корректное освобождение ресурсов журналирования
        logger.close()
        if logger.failures:
            print(f"Внимание: зафиксировано ошибок записи в лог: {len(logger.failures)}", file=sys.stderr)
            exit_code = 1
            
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
