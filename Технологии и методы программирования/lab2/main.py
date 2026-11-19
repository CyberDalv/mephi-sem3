from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import platform
import sys
from enum import Enum
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Callable

from worker import PrimeStats, analyze_range, merge_stats


DEFAULT_LIMIT: int = 300_000
DEFAULT_REPEATS: int = 5
DEFAULT_WORKERS: tuple[int, ...] = (1, 2, 4)
EXPECTED = PrimeStats(25997, 299993, 709507093)


class RunMode(str, Enum):
    # 1 Добавить check, sequential, processes, experiment.
    check = "check"
    sequential = "sequential"
    processes = "processes"
    experiment = "experiment"


class StartMethod(str, Enum):
    # 2 Добавить spawn и fork.
    spawn = "spawn"
    fork = "fork"


def build_parser() -> argparse.ArgumentParser:
    """Создать CLI по установленному контракту."""
    # 3 Настроить все аргументы, choices, defaults и help.
    parser = argparse.ArgumentParser(description="Лабораторная работа 2: Многопроцессорность")
    parser.add_argument("--mode", type=RunMode, choices=list(RunMode), required=True, help="Режим запуска")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Верхняя граница диапазона")
    parser.add_argument("--workers", type=int, nargs="+", default=list(DEFAULT_WORKERS), help="Количество процессов")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS, help="Количество измерений")
    parser.add_argument("--start-method", type=StartMethod, choices=list(StartMethod), default=StartMethod.spawn, help="Метод multiprocessing")
    parser.add_argument("--include-fork", action="store_true", help="Дополнительная серия fork")
    parser.add_argument("--output", type=Path, default=Path("results/metrics.json"), help="Путь к metrics.json")
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Завершить разбор с ошибкой для недопустимых сочетаний."""
    # 4 Проверить limit, repeats, workers и доступность метода.
    if args.limit < 1000:
        parser.error("limit должен быть не меньше 1000")
    if args.repeats < 3:
        parser.error("repeats должен быть не меньше 3")
    for w in args.workers:
        if not (1 <= w <= 8):
            parser.error(f"Количество процессов (workers) должно быть от 1 до 8, передано {w}")
    if args.start_method == StartMethod.fork and not hasattr(mp, 'get_context'):
        parser.error("Метод fork не поддерживается на данной платформе")


def split_ranges(limit: int, part_count: int) -> list[tuple[int, int]]:
    """Разбить закрытый диапазон 2..limit без пропусков."""
    # 5 Учесть остаток от деления и маленькие диапазоны.
    total = limit - 1  # От 2 до limit
    # Защита: не создавать диапазонов больше, чем самих чисел
    part_count = min(part_count, total)
    base_size = total // part_count
    remainder = total % part_count

    ranges = []
    current_start = 2
    for i in range(part_count):
        size = base_size + (1 if i < remainder else 0)
        current_end = current_start + size - 1
        ranges.append((current_start, current_end))
        current_start = current_end + 1
        
    return ranges


def run_sequential(limit: int) -> PrimeStats:
    # 6 Вызвать analyze_range ровно один раз.
    return analyze_range((2, limit))


def run_processes(limit: int, workers: int, method: StartMethod) -> PrimeStats:
    """Выполнить задачу через контекст multiprocessing."""
    # 7 Получить контекст mp.get_context(method.value).
    ctx = mp.get_context(method.value)
    ranges = split_ranges(limit, workers)
    
    # 8 Создать Pool требуемого размера и применить map.
    with ctx.Pool(processes=workers) as pool:
        results = pool.map(analyze_range, ranges)
        
    # 9 Объединить частичные результаты через merge_stats.
    return merge_stats(results)


def measure(action: Callable[[], PrimeStats], repeats: int) -> tuple[list[float], PrimeStats]:
    """Измерить action несколько раз и вернуть последний результат."""
    durations = []
    last_result = None
    results_list = []
    
    # 10 Для каждого повтора использовать perf_counter до и после.
    for _ in range(repeats):
        start = perf_counter()
        last_result = action()
        durations.append(perf_counter() - start)
        results_list.append(last_result)
        
    # 11 Проверить равенство результатов всех повторов.
    if any(r != last_result for r in results_list):
        raise RuntimeError("Результаты повторов не совпадают между собой!")
        
    return durations, last_result


def build_metrics(args: argparse.Namespace) -> dict[str, object]:
    """Провести эксперимент и построить словарь установленной схемы."""
    # 12 Измерить sequential и spawn для каждого workers.
    seq_durations, seq_result = measure(lambda: run_sequential(args.limit), args.repeats)
    seq_median = median(seq_durations)
    
    process_runs = []
    all_process_results_match = True
    
    for w in args.workers:
        dur, res = measure(lambda: run_processes(args.limit, w, StartMethod.spawn), args.repeats)
        med = median(dur)
        speedup = seq_median / med
        eff = speedup / w
        match = (res == seq_result)
        if not match:
            all_process_results_match = False
            
        process_runs.append({
            "start_method": "spawn",
            "workers": w,
            "durations_seconds": dur,
            "median_seconds": med,
            "speedup": speedup,
            "efficiency": eff,
            "result_matches_sequential": match
        })
        
    # 14 При --include-fork выполнить или отметить unsupported.
    fork_run = {
        "status": "not_requested",
        "workers": 4,
        "durations_seconds": [],
        "median_seconds": None,
        "fork_to_spawn_ratio": None,
        "result_matches_sequential": None
    }
    
    if args.include_fork:
        if hasattr(mp, "get_context") and 'fork' in mp.get_all_start_methods():
            fdur, fres = measure(lambda: run_processes(args.limit, 4, StartMethod.fork), args.repeats)
            fmed = median(fdur)
            spawn_4_med = next((pr["median_seconds"] for pr in process_runs if pr["workers"] == 4 and pr["start_method"] == "spawn"), None)
            
            fork_run.update({
                "status": "completed",
                "durations_seconds": fdur,
                "median_seconds": fmed,
                "fork_to_spawn_ratio": fmed / spawn_4_med if spawn_4_med else None,
                "result_matches_sequential": (fres == seq_result)
            })
        else:
            fork_run["status"] = "unsupported"

    # 15 Добавить среду, параметры и проверки корректности.
    return {
        "environment": {
            "operating_system": platform.system(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "available_start_methods": mp.get_all_start_methods()
        },
        "experiment": {
            "limit": args.limit,
            "repeats": args.repeats,
            "worker_counts": args.workers,
            "required_start_method": "spawn"
        },
        "expected_result": {
            "count": EXPECTED.count,
            "max_prime": EXPECTED.max_prime,
            "checksum": EXPECTED.checksum
        },
        "sequential": {
            "durations_seconds": seq_durations,
            "median_seconds": seq_median,
            "result_matches_expected": seq_result == EXPECTED
        },
        "process_runs": process_runs,
        "fork_run": fork_run
    }


def write_metrics(path: Path, metrics: dict[str, object]) -> None:
    # 16 Создать родительский каталог и записать UTF-8 JSON.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)


def main() -> int:
    # 17 Разобрать и проверить аргументы.
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)

    # 18 Выполнить выбранный RunMode.
    if args.mode == RunMode.check:
        res = run_sequential(args.limit)
        print(f"check mode: count={res.count}, max_prime={res.max_prime}, checksum={res.checksum}, matches_expected={res == EXPECTED}")
        return 0
        
    elif args.mode == RunMode.sequential:
        _, res = measure(lambda: run_sequential(args.limit), args.repeats)
        print(f"sequential mode completed.")
        return 0
        
    elif args.mode == RunMode.processes:
        _, res = measure(lambda: run_processes(args.limit, args.workers[0], args.start_method), args.repeats)
        print("processes mode completed.")
        return 0
        
    elif args.mode == RunMode.experiment:
        metrics = build_metrics(args)
        # 20 Для experiment записать metrics.json.
        write_metrics(args.output, metrics)
        
        # 19 Вывести итог без служебных сообщений дочерних процессов.
        print("Лабораторная работа 2")
        print(f"Операционная система: {platform.system()}")
        print(f"Python: {platform.python_version()}")
        print(f"Методы запуска: {', '.join(mp.get_all_start_methods())}")
        print(f"Диапазон: 2..{args.limit}")
        print(f"Повторы: {args.repeats}")
        print(f"Последовательно, медиана: {metrics['sequential']['median_seconds']:.4f} с")
        print("spawn | Процессы | Медиана, с | Ускорение | Эффективность")
        
        all_match = True
        for pr in metrics["process_runs"]:
            print(f"      | {pr['workers']:8d} | {pr['median_seconds']:10.4f} | {pr['speedup']:9.4f} | {pr['efficiency']:13.4f}")
            if not pr["result_matches_sequential"]:
                all_match = False
                
        print(f"Результаты процессов совпадают: {all_match}")
        print(f"fork: {metrics['fork_run']['status']}")
        print(f"Метрики записаны в: {args.output}")
        return 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())