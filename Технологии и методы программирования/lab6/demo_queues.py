from __future__ import annotations
import queue
import threading
from queued_logger import QueuedLogger, STOP

def producer(q: queue.Queue, thread_id: int, count: int) -> None:
    for i in range(count):
        event = {
            "time": "2026-10-09T00:00:00+00:00",
            "command": "demo",
            "args": [f"demo-{thread_id}-{i:03d}"],
            "result": "OK",
            "detail": "test"
        }
        q.put(event)

def run_demos() -> None:
    print("--- Запуск демонстрации очередей ---")
    log_file = "test_demo_queues.jsonl"
    
    # 1. Проверка 4 потоков по 25 событий
    logger = QueuedLogger(log_file, maxsize=20)
    logger.start()
    
    threads = []
    for t_id in range(4):
        t = threading.Thread(target=producer, args=(logger.queue, t_id, 25))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    logger.close()
    
    lines = open(log_file, "r", encoding="utf-8").readlines()
    print(f"Успешно записано строк через фоновый поток: {len(lines)} (ожидается 100)")
    assert len(lines) == 100
    print("Демонстрация потоковой очереди успешно пройдена!")

if __name__ == "__main__":
    run_demos()
