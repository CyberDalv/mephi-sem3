from __future__ import annotations

import json
import platform
import subprocess
import sys
import threading
from dataclasses import asdict
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Callable

from worker import FileStats, analyze_file


ROOT_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = ROOT_DIR / "data"
RESULTS_DIR: Path = ROOT_DIR / "results"
WORKER_PATH: Path = ROOT_DIR / "worker.py"

FILE_COUNT: int = 12
REPEATS: int = 7
THREAD_COUNTS: tuple[int, ...] = (1, 2, 4, 8)
ARTIFICIAL_DELAY_SECONDS: float = 0.12


def prepare_test_files() -> list[Path]:
    """Создать единый набор входных файлов."""
    
    # 1. Создать DATA_DIR с exist_ok=True.
    DATA_DIR.mkdir(exist_ok=True)
    paths = []
    
    for file_number in range(FILE_COUNT):
        file_name = f"input_{file_number:02d}.txt"
        file_path = DATA_DIR / file_name
        
        lines = []
        for line_number in range(300 + file_number):
            # Символ \n в конце нужен, чтобы выйти на точное количество символов (219960).
            lines.append(f"Файл {file_number:02d}, строка {line_number:04d}. Алгоритмы, структуры данных и Python.\n")
            
        file_path.write_text("".join(lines), encoding="utf-8")
        paths.append(file_path)
        
    return paths


def run_sequential(paths: list[Path]) -> list[FileStats]:
    """Обработать все файлы последовательно."""
    
    return [analyze_file(path, ARTIFICIAL_DELAY_SECONDS) for path in paths]


def run_threaded(
    paths: list[Path],
    thread_count: int,
) -> list[FileStats]:
    """Обработать файлы в указанном количестве потоков."""
    
    result_slots: list[FileStats | None] = [None] * len(paths)
    result_lock: threading.Lock = threading.Lock()

    def thread_job(thread_number: int) -> None:
        index = thread_number
        while index < len(paths):
            res = analyze_file(paths[index], ARTIFICIAL_DELAY_SECONDS)
            with result_lock:
                result_slots[index] = res
            index += thread_count

    threads = []
    for i in range(thread_count):
        t = threading.Thread(target=thread_job, args=(i,), name=f"WorkerThread-{i}")
        threads.append(t)
        
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    if any(r is None for r in result_slots):
        raise RuntimeError("Ошибка: не все файлы были обработаны.")
        
    return [r for r in result_slots if r is not None]


def measure_action(
    action: Callable[[], list[FileStats]],
) -> tuple[list[float], list[FileStats]]:
    """Выполнить action REPEATS раз и вернуть времена и результат."""
    
    durations = []
    last_result = []
    
    for _ in range(REPEATS):
        start = perf_counter()
        last_result = action()
        end = perf_counter()
        durations.append(end - start)
        
    return durations, last_result


def run_external_worker(path: Path) -> dict[str, object]:
    """Запустить worker.py отдельным процессом."""
    
    command: list[str] = [
        sys.executable,
        str(WORKER_PATH),
        str(path),
        "0",
    ]
    
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    return json.loads(completed.stdout)


def main() -> int:
    """Выполнить эксперимент и сохранить результаты."""
    paths = prepare_test_files()
    
    seq_durations, seq_result = measure_action(lambda: run_sequential(paths))
    seq_median = median(seq_durations)
    
    thread_experiments_results = []
    all_thread_results_match = True
    
    for t_count in THREAD_COUNTS:
        durations, result = measure_action(lambda: run_threaded(paths, t_count))
        t_median = median(durations)
        speedup = seq_median / t_median
        efficiency = speedup / t_count
        
        matches = (result == seq_result)
        if not matches:
            all_thread_results_match = False
            
        thread_experiments_results.append({
            "thread_count": t_count,
            "durations_seconds": durations,
            "median_seconds": t_median,
            "speedup": speedup,
            "efficiency": efficiency,
            "result_matches_sequential": matches
        })
        
    subprocess_durations = []
    subprocess_result = None
    
    for _ in range(REPEATS):
        start = perf_counter()
        subprocess_result = run_external_worker(paths[0])
        end = perf_counter()
        subprocess_durations.append(end - start)
        
    subprocess_median = median(subprocess_durations)
    subprocess_correct = (subprocess_result == asdict(analyze_file(paths[0], 0)))
    
    total_files = len(seq_result)
    total_lines = sum(r.lines for r in seq_result)
    total_words = sum(r.words for r in seq_result)
    total_chars = sum(r.characters for r in seq_result)

    metrics = {
        "environment": {
            "operating_system": platform.system(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable
        },
        "experiment": {
            "file_count": FILE_COUNT,
            "repeats": REPEATS,
            "artificial_delay_seconds": ARTIFICIAL_DELAY_SECONDS,
            "thread_counts": list(THREAD_COUNTS)
        },
        "sequential": {
            "durations_seconds": seq_durations,
            "median_seconds": seq_median
        },
        "thread_experiments": thread_experiments_results,
        "subprocess": {
            "durations_seconds": subprocess_durations,
            "median_seconds": subprocess_median,
            "result_is_correct": subprocess_correct
        },
        "correctness": {
            "all_thread_results_match": all_thread_results_match,
            "subprocess_result_matches": subprocess_correct
        },
        "totals": {
            "files": total_files,
            "lines": total_lines,
            "words": total_words,
            "characters": total_chars
        }
    }
    
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print("Лабораторная работа 1")
    print(f"Операционная система: {platform.system()}")
    print(f"Python: {platform.python_version()}")
    print(f"Количество файлов: {FILE_COUNT}")
    print(f"Количество повторов: {REPEATS}\n")
    print(f"Последовательно, медиана: {seq_median:.4f} с\n")
    print("Потоки | Медиана, с | Ускорение | Эффективность")
    for t_data in thread_experiments_results:
        print(f"{t_data['thread_count']:6d} | {t_data['median_seconds']:10.4f} | {t_data['speedup']:9.4f} | {t_data['efficiency']:13.4f}")
        
    print(f"\nРезультаты потоков совпадают: {all_thread_results_match}")
    print(f"Результат subprocess совпадает: {subprocess_correct}")
    print("Метрики записаны в: results/metrics.json")
    
    if not (all_thread_results_match and subprocess_correct):
        return 1
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())