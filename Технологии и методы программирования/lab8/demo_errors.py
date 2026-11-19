from __future__ import annotations
import os
from pathlib import Path
from unittest.mock import patch
from shell import FileManagerShell
from queued_logger import QueuedLogger

def run_demos() -> None:
    print("=== ДЕМОНСТРАЦИЯ ЛАБОРАТОРНОЙ РАБОТЫ №7 ===")
    
    # Подготовка учебного workspace
    ws = Path("workspace")
    ws.mkdir(exist_ok=True)
    
    source = ws / "source.txt"
    source.write_text("hello source", encoding="utf-8")
    
    occupied = ws / "occupied.txt"
    occupied.write_text("hello occupied", encoding="utf-8")
    
    folder = ws / "folder"
    folder.mkdir(exist_ok=True)

    log_file = "demo_command_log.jsonl"
    if Path(log_file).exists():
        Path(log_file).unlink()

    logger = QueuedLogger(log_file, maxsize=20)
    logger.start()
    
    shell = FileManagerShell(logger=logger)

    print("\n1. Проверка штатной команды cd:")
    shell.onecmd("cd folder")
    shell.onecmd("cd ..")

    print("\n2. Проверка ожидаемого отказа (FileNotFoundError для cd missing):")
    shell.onecmd("cd missing_folder")

    print("\n3. Проверка FileExistsError для cp source.txt occupied.txt:")
    shell.onecmd("cp source.txt occupied.txt")

    print("\n4. Проверка WorkspaceViolationError (выход за workspace):")
    shell.onecmd("cp source.txt ../outside_file.txt")

    print("\n5. Демонстрация PermissionError через unittest.mock:")
    with patch("file_ops.shutil.copy2", side_effect=PermissionError("учебный отказ записи")):
        shell.onecmd("cp source.txt denied_copy.txt")

    print("\n6. Проверка разбора shlex с незакрытой кавычкой:")
    shell.onecmd('cd "folder_without_closing_quote')

    logger.close()
    print(f"\nДемонстрации завершены. Журнал записан в {log_file}.")

if __name__ == "__main__":
    run_demos()
