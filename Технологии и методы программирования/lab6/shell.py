from __future__ import annotations
import cmd
import shlex
import os
import multiprocessing
from pathlib import Path
from datetime import datetime, timezone
from command_history import CommandHistory
from queued_logger import QueuedLogger
from hash_workers import hash_worker

class FileManagerShell(cmd.Cmd):
    prompt = "file_manager> "

    def __init__(self, logger: QueuedLogger) -> None:
        super().__init__()
        self.logger = logger
        self.history = CommandHistory(maxlen=5)
        self.workspace = Path("workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.current_dir = self.workspace

    def _resolve(self, path_str: str, must_exist: bool = False) -> Path:
        path = (self.current_dir / path_str).resolve()
        if not str(path).startswith(str(self.workspace)):
            raise ValueError("Объект за пределами workspace")
        if must_exist and not path.exists():
            raise FileNotFoundError("Объект не найден")
        return path

    def _log_and_record(self, command: str, args: list[str] | None, result: str, detail: str) -> None:
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "command": command.lower().strip(),
            "args": args,
            "result": result,
            "detail": detail
        }
        self.history.append(event)
        self.logger.submit(event)

    def onecmd(self, line: str) -> bool:
        line_stripped = line.strip()
        if not line_stripped:
            return False

        try:
            parts = shlex.split(line_stripped)
            cmd_name = parts[0].lower()
        except Exception as e:
            self._log_and_record("unknown", None, "ERROR", str(e))
            print(f"ERROR: {e}")
            return False

        if not hasattr(self, f"do_{cmd_name}") and cmd_name != "EOF":
            self._log_and_record(cmd_name, parts[1:] if len(parts) > 1 else [], "ERROR", f"неизвестная команда: {cmd_name}")
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
            self._log_and_record("pwd", args, "OK", "успешно")
        except Exception as e:
            self._log_and_record("pwd", args, "ERROR", str(e))
            print(f"ERROR pwd: {e}")

    def do_ls(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            target = self._resolve(args[0], must_exist=True) if args else self.current_dir
            if not target.is_dir():
                raise NotADirectoryError("не является каталогом")
            for item in target.iterdir():
                print(item.name)
            self._log_and_record("ls", args, "OK", "успешно")
        except Exception as e:
            self._log_and_record("ls", args, "ERROR", str(e))
            print(f"ERROR ls: {e}")

    def do_cd(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            if not args:
                raise ValueError("укажите каталог")
            target = self._resolve(args[0], must_exist=True)
            if not target.is_dir():
                raise NotADirectoryError("не является каталогом")
            self.current_dir = target
            self._log_and_record("cd", args, "OK", "успешно")
        except Exception as e:
            self._log_and_record("cd", args, "ERROR", str(e))
            print(f"ERROR cd: {e}")

    def do_history(self, arg: str) -> None:
        """history: показать последние завершенные команды."""
        args = shlex.split(arg) if arg else []
        try:
            if args:
                raise ValueError("history не принимает аргументы")
            
            # Снимаем текущую историю ДО добавления самой команды history
            snapshot = self.history.get_snapshot()
            for ev in snapshot:
                print(f"[{ev['time']}] {ev['command']} {ev['args']} -> {ev['result']} ({ev['detail']})")
            
            self._log_and_record("history", args, "OK", "успешно")
        except Exception as e:
            self._log_and_record("history", args, "ERROR", str(e))
            print(f"ERROR history: {e}")

    def do_hash(self, arg: str) -> None:
        """hash ПУТЬ [ПУТЬ ...]: вычислить SHA-256 файлов с помощью процессов."""
        args = shlex.split(arg) if arg else []
        try:
            if not args:
                raise ValueError("укажите хотя бы один путь")

            valid_tasks = []
            errors_count = 0
            
            for idx, raw_path in enumerate(args):
                try:
                    resolved_p = self._resolve(raw_path, must_exist=True)
                    if not resolved_p.is_file():
                        raise IsADirectoryError("объект не является обычным файлом")
                    valid_tasks.append({"task_id": idx, "path": str(resolved_p)})
                except Exception as ex:
                    errors_count += 1
                    print(f"[{idx}] Ошибка для {raw_path}: {ex}")

            if valid_tasks:
                ctx = multiprocessing.get_context("spawn")
                task_queue = ctx.Queue()
                result_queue = ctx.Queue()

                workers = []
                for _ in range(2):
                    p = ctx.Process(target=hash_worker, args=(task_queue, result_queue, os.getpid())) # Учебный PID процесса воркера отобразим через os.getpid в воркере
                    p.start()
                    workers.append(p)

                for t in valid_tasks:
                    task_queue.put(t)
                for _ in workers:
                    task_queue.put(None)

                results_map = {}
                expected_count = len(valid_tasks)
                
                while len(results_map) < expected_count:
                    try:
                        res = result_queue.get(timeout=30)
                        results_map[res["task_id"]] = res
                    except Exception:
                        break

                for p in workers:
                    p.join(timeout=2)
                    if p.is_alive():
                        p.terminate()
                        p.join()

                task_queue.close()
                task_queue.join_thread()
                result_queue.close()
                result_queue.join_thread()

                for idx, raw_path in enumerate(args):
                    if idx in results_map:
                        r = results_map[idx]
                        if r["result"] == "OK":
                            print(f"{raw_path} -> {r['sha256']} (worker PID: {r['worker_pid']})")
                        else:
                            errors_count += 1
                            print(f"{raw_path} -> ERROR: {r['detail']}")

            status = "OK" if errors_count == 0 else "ERROR"
            self._log_and_record("hash", args, status, f"успешно: {len(args)-errors_count}, ошибок: {errors_count}")
        except Exception as e:
            self._log_and_record("hash", args, "ERROR", str(e))
            print(f"ERROR hash: {e}")

    def do_help(self, arg: str) -> None:
        args = shlex.split(arg) if arg else []
        try:
            super().do_help(arg)
            self._log_and_record("help", args, "OK", "успешно")
        except Exception as e:
            self._log_and_record("help", args, "ERROR", str(e))
            print(f"ERROR help: {e}")

    def do_exit(self, arg: str) -> bool:
        args = shlex.split(arg) if arg else []
        self._log_and_record("exit", args, "OK", "выход из менеджера")
        print("Выход.")
        return True

    def do_EOF(self, arg: str) -> bool:
        print()
        return self.do_exit(arg)
