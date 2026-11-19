from __future__ import annotations
import cmd
import shlex
import os
import multiprocessing
from pathlib import Path
from datetime import datetime, timezone
from errors import FileManagerError
from file_ops import FileManagerCore
from command_history import CommandHistory
from queued_logger import QueuedLogger
from hash_workers import hash_worker

class FileManagerShell(cmd.Cmd):
    prompt = "file_manager> "

    def __init__(self, logger: QueuedLogger) -> None:
        super().__init__()
        self.logger = logger
        self.core = FileManagerCore()
        self.history = CommandHistory(maxlen=5)

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

    def run_file_action(self, action, args):
        """Единый диспетчер выполнения операции с блоками try-except-else."""
        try:
            detail = action(*args)
        except FileManagerError as exc:
            return "ERROR", f"{type(exc).__name__}: {exc}"
        except FileNotFoundError as exc:
            return "ERROR", f"FileNotFoundError: {exc}"
        except PermissionError as exc:
            return "ERROR", f"PermissionError: {exc}"
        except FileExistsError as exc:
            return "ERROR", f"FileExistsError: {exc}"
        except IsADirectoryError as exc:
            return "ERROR", f"IsADirectoryError: {exc}"
        except NotADirectoryError as exc:
            return "ERROR", f"NotADirectoryError: {exc}"
        except OSError as exc:
            return "ERROR", f"{type(exc).__name__}: {exc}"
        except Exception:
            # Неожиданные ошибки реализации (например, RuntimeError) пробрасываются наружу с traceback
            raise
        else:
            return "OK", str(detail or "Операция выполнена")

    def onecmd(self, line: str) -> bool:
        line_stripped = line.strip()
        if not line_stripped:
            return False

        # Разбор строки с узким перехватом ValueError (например, незакрытые кавычки)
        try:
            parts = shlex.split(line_stripped)
            cmd_name = parts[0].lower()
            args = parts[1:]
        except ValueError as e:
            self._log_and_record("unknown", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: ошибка разбора аргументов: {e}")
            return False

        if not hasattr(self, f"do_{cmd_name}") and cmd_name != "EOF":
            self._log_and_record(cmd_name, args, "ERROR", f"неизвестная команда: {cmd_name}")
            print(f"ERROR: неизвестная команда '{cmd_name}'")
            return False

        return super().onecmd(line_stripped)

    def do_pwd(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("pwd", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if parts:
            result, detail = "ERROR", "OperationRejectedError: Команда pwd не принимает аргументы"
        else:
            result, detail = self.run_file_action(self.core.cmd_pwd, [])
            if result == "OK":
                print(detail)

        if result == "ERROR":
            print(f"ERROR pwd: {detail}")
        self._log_and_record("pwd", parts, result, detail)

    def do_ls(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("ls", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if len(parts) > 1:
            result, detail = "ERROR", "OperationRejectedError: Слишком много аргументов для ls"
        else:
            result, detail = self.run_file_action(self.core.cmd_ls, parts)
            if result == "OK":
                for item in eval(detail) if detail.startswith("[") else []: # Или вывод списка напрямую
                    pass
                # Простейший вывод
                items = self.core.cmd_ls(parts[0] if parts else None)
                for it in items:
                    print(it)

        if result == "ERROR":
            print(f"ERROR ls: {detail}")
        self._log_and_record("ls", parts, result, detail)

    def do_cd(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("cd", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if len(parts) != 1:
            result, detail = "ERROR", "OperationRejectedError: Требуется ровно один аргумент для cd"
        else:
            result, detail = self.run_file_action(self.core.cmd_cd, parts)
            if result == "OK":
                print(detail)

        if result == "ERROR":
            print(f"ERROR cd: {detail}")
        self._log_and_record("cd", parts, result, detail)

    def do_cp(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("cp", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if len(parts) != 2:
            result, detail = "ERROR", "OperationRejectedError: Требуется ровно два аргумента для cp"
        else:
            result, detail = self.run_file_action(self.core.cmd_cp, parts)
            if result == "OK":
                print(detail)

        if result == "ERROR":
            print(f"ERROR cp: {detail}")
        self._log_and_record("cp", parts, result, detail)

    def do_mv(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("mv", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if len(parts) != 2:
            result, detail = "ERROR", "OperationRejectedError: Требуется ровно два аргумента для mv"
        else:
            result, detail = self.run_file_action(self.core.cmd_mv, parts)
            if result == "OK":
                print(detail)

        if result == "ERROR":
            print(f"ERROR mv: {detail}")
        self._log_and_record("mv", parts, result, detail)

    def do_rm(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("rm", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if len(parts) != 1:
            result, detail = "ERROR", "OperationRejectedError: Требуется ровно один аргумент для rm"
        else:
            result, detail = self.run_file_action(self.core.cmd_rm, parts)
            if result == "OK":
                print(detail)

        if result == "ERROR":
            print(f"ERROR rm: {detail}")
        self._log_and_record("rm", parts, result, detail)

    def do_history(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("history", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if parts:
            result, detail = "ERROR", "OperationRejectedError: history не принимает аргументов"
        else:
            snapshot = self.history.get_snapshot()
            for ev in snapshot:
                print(f"[{ev['time']}] {ev['command']} {ev['args']} -> {ev['result']} ({ev['detail']})")
            result, detail = "OK", "успешно"

        if result == "ERROR":
            print(f"ERROR history: {detail}")
        self._log_and_record("history", parts, result, detail)

    def do_hash(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError as e:
            self._log_and_record("hash", None, "ERROR", f"ValueError: {e}")
            print(f"ERROR: {e}")
            return

        if not parts:
            result, detail = "ERROR", "OperationRejectedError: укажите хотя бы один путь для hash"
            print(f"ERROR hash: {detail}")
            self._log_and_record("hash", parts, result, detail)
            return

        valid_tasks = []
        errors_count = 0
        for idx, raw_path in enumerate(parts):
            try:
                resolved_p = self.core.resolve_path(raw_path, must_exist=True)
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
                p = ctx.Process(target=hash_worker, args=(task_queue, result_queue, os.getpid()))
                p.start()
                workers.append(p)

            for t in valid_tasks:
                task_queue.put(t)
            for _ in workers:
                task_queue.put(None)

            results_map = {}
            for _ in range(len(valid_tasks)):
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

            for idx, raw_path in enumerate(parts):
                if idx in results_map:
                    r = results_map[idx]
                    if r["result"] == "OK":
                        print(f"{raw_path} -> {r['sha256']} (worker PID: {r['worker_pid']})")
                    else:
                        errors_count += 1
                        print(f"{raw_path} -> ERROR: {r['detail']}")

        status = "OK" if errors_count == 0 else "ERROR"
        detail = f"успешно: {len(parts)-errors_count}, ошибок: {errors_count}"
        self._log_and_record("hash", parts, status, detail)

    def do_help(self, arg: str) -> None:
        try:
            parts = shlex.split(arg)
        except ValueError:
            parts = []
        super().do_help(arg)
        self._log_and_record("help", parts, "OK", "успешно")

    def do_exit(self, arg: str) -> bool:
        self._log_and_record("exit", [], "OK", "выход из менеджера")
        print("Выход.")
        return True

    def do_EOF(self, arg: str) -> bool:
        print()
        return self.do_exit(arg)
