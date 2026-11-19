from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any

def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()

def hash_worker(task_queue: Any, result_queue: Any, worker_pid: int) -> None:
    while True:
        task = task_queue.get()
        if task is None:
            break
        
        task_id = task["task_id"]
        path_str = task["path"]
        
        try:
            digest = sha256_file(path_str)
            result_queue.put({
                "task_id": task_id,
                "worker_pid": worker_pid,
                "result": "OK",
                "sha256": digest,
                "detail": ""
            })
        except OSError as e:
            result_queue.put({
                "task_id": task_id,
                "worker_pid": worker_pid,
                "result": "ERROR",
                "sha256": None,
                "detail": str(e)
            })
