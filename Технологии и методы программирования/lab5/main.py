from __future__ import annotations
import sys
from shell import FileManagerShell
from command_log import CommandLogger

def main() -> int:
    logger = CommandLogger("command_log.jsonl")
    app = FileManagerShell(logger=logger)
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print("\nЗавершение работы.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
