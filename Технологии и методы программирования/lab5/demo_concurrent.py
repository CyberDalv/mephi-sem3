from __future__ import annotations
import json
import threading
from pathlib import Path
from command_log import CommandLogger

class MonitoredCommandLogger(CommandLogger):
    def __init__(self, log_path: Path | str) -> None:
        super().__init__(log_path)
        self.active_writers = 0
        self.max_active_writers = 0
        self.monitor_lock = threading.Lock()

    def append(self, command: str, args: list[str] | None, result: str, detail: str) -> None:
        record = {
            "time": "2026-10-02T10:31:22+00:00",
            "command": command,
            "args": args,
            "result": result,
            "detail": detail
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        
        with self.semaphore:
            with self.monitor_lock:
                self.active_writers += 1
                if self.active_writers > self.max_active_writers:
                    self.max_active_writers = self.active_writers
            
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(line)
            finally:
                with self.monitor_lock:
                    self.active_writers -= 1

def worker(logger: MonitoredCommandLogger, thread_id: int, count_per_thread: int) -> None:
    for i in range(count_per_thread):
        idx = thread_id * count_per_thread + i
        logger.append("demo", [f"demo-{idx:03d}"], "OK", "concurrent test")

def run_demo() -> None:
    log_file = Path("test_concurrent_log.jsonl")
    if log_file.exists():
        log_file.unlink()

    logger = MonitoredCommandLogger(log_file)
    threads: list[threading.Thread] = []
    num_threads = 4
    per_thread = 25

    for t_id in range(num_threads):
        t = threading.Thread(target=worker, args=(logger, t_id, per_thread))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    lines = log_file.read_text(encoding="utf-8").splitlines()
    print(f"Всего записано строк: {len(lines)}")

    unique_ids = set()
    json_errors = 0

    for line in lines:
        try:
            data = json.loads(line)
            assert "time" in data
            assert "command" in data
            assert "args" in data
            assert "result" in data
            assert "detail" in data
            
            arg_val = data["args"][0]
            unique_ids.add(arg_val)
        except Exception:
            json_errors += 1

    print(f"Ошибок JSON: {json_errors}")
    print(f"Уникальных номеров: {len(unique_ids)} из 100")
    print(f"Максимум одновременных писателей (max_active_writers): {logger.max_active_writers}")

    assert len(unique_ids) == 100, "Должно быть ровно 100 уникальных записей!"
    assert logger.max_active_writers == 1, "Максимум одновременных писателей должен быть равен 1!"
    print("Конкурентная проверка успешно пройдена!")

if __name__ == "__main__":
    run_demo()
