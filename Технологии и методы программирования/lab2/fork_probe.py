from __future__ import annotations

import json
import os
import sys

INHERITED_VALUE: int = 314_159


def run_probe() -> dict[str, object]:
    """Проверить fork и вернуть единый JSON-совместимый результат."""
    # 1 Вернуть status=unsupported и понятную причину.
    if not hasattr(os, "fork"):
        return {"status": "unsupported", "reason": "os.fork is not available on this OS"}

    # 2 Создать os.pipe до fork.
    r, w = os.pipe()
    
    pid = os.fork()
    
    if pid == 0:
        # Дочерний процесс
        # 3 В дочерней ветви закрыть read descriptor.
        os.close(r)
        
        # 4 Передать через pipe PID, PPID и INHERITED_VALUE.
        child_data = {
            "child_pid": os.getpid(),
            "child_parent_pid": os.getppid(),
            "inherited_value": INHERITED_VALUE
        }
        with os.fdopen(w, 'w') as f:
            json.dump(child_data, f)
            
        # 5 Завершить дочерний процесс через os._exit(0).
        os._exit(0)
    else:
        # Родительский процесс
        # 6 В родительской ветви закрыть write descriptor.
        os.close(w)
        
        # 7 Прочитать JSON, вызвать os.waitpid и проверить exit code.
        with os.fdopen(r, 'r') as f:
            child_data = json.load(f)
            
        _, status = os.waitpid(pid, 0)
        # Обработка кода возврата (сдвиг вправо на 8 бит)
        exit_code = status >> 8
        
        # 8 Вернуть status=supported и данные обеих ветвей.
        return {
            "status": "supported",
            "parent_pid": os.getpid(),
            "child_data": child_data,
            "exit_code": exit_code
        }


def main() -> int:
    # 9 Вывести ровно одну JSON-строку в UTF-8.
    result = run_probe()
    print(json.dumps(result, ensure_ascii=False))
    # 10 Вернуть 0 для supported и unsupported.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())