from __future__ import annotations
import cmd
import shlex
from pathlib import Path
from command_log import CommandLogger

class FileManagerShell(cmd.Cmd):
    prompt = "file_manager> "

    def __init__(self, logger: CommandLogger | None = None) -> None:
        super().__init__()
        self.logger = logger or CommandLogger("command_log.jsonl")
        self.workspace = Path("workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.current_dir = self.workspace

    def _resolve(self, path_str: str) -> Path:
        path = (self.current_dir / path_str).resolve()
        if not str(path).startswith(str(self.workspace)):
            raise ValueError("Объект за пределами workspace")
        return path

    def onecmd(self, line: str) -> bool:
        line_stripped = line.strip()
        if not line_stripped:
            return False

        try:
            parts = shlex.split(line_stripped)
            cmd_name = parts[0].lower()
        except Exception as e:
            self.logger.append("unknown", None, "ERROR", str(e))
            print(f"ERROR: {e}")
            return False

        if not hasattr(self, f"do_{cmd_name}") and cmd_name != "EOF":
            self.logger.append(cmd_name, parts[1:] if len(parts) > 1 else [], "ERROR", f"неизвестная команда: {cmd_name}")
            print(f"ERROR: неизвестная команда '{cmd_name}'")
            return False

        return super().onecmd(line_stripped)

    def do_pwd(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            if args:
                raise ValueError("Команда pwd не принимает аргументы")
            rel_path = self.current_dir.relative_to(self.workspace)
            print(f"/{rel_path}" if str(rel_path) != "." else "/")
            self.logger.append("pwd", args, "OK", "успешно")
        except Exception as e:
            self.logger.append("pwd", args, "ERROR", str(e))
            print(f"ERROR pwd: {e}")

    def do_ls(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            target = self._resolve(args[0]) if args else self.current_dir
            if not target.exists():
                raise OSError("путь не найден")
            for item in target.iterdir():
                print(item.name)
            self.logger.append("ls", args, "OK", "успешно")
        except Exception as e:
            self.logger.append("ls", args, "ERROR", str(e))
            print(f"ERROR ls: {e}")

    def do_cd(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            if not args:
                raise ValueError("укажите каталог")
            target = self._resolve(args[0])
            if not target.is_dir():
                raise NotADirectoryError("не является каталогом")
            self.current_dir = target
            self.logger.append("cd", args, "OK", "успешно")
        except Exception as e:
            self.logger.append("cd", args, "ERROR", str(e))
            print(f"ERROR cd: {e}")

    def do_help(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            super().do_help(arg)
            self.logger.append("help", args, "OK", "успешно")
        except Exception as e:
            self.logger.append("help", args, "ERROR", str(e))
            print(f"ERROR help: {e}")

    def do_exit(self, arg: str) -> bool:
        args = shlex.split(arg) if arg else []
        try:
            self.logger.append("exit", args, "OK", "выход из менеджера")
            print("Выход.")
            return True
        except Exception as e:
            self.logger.append("exit", args, "ERROR", str(e))
            return True

    def do_EOF(self, arg: str) -> bool:
        print()
        return self.do_exit(arg)
