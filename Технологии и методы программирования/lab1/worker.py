from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileStats:
    file_name: str
    lines: int
    words: int
    characters: int


def analyze_file(
    path: Path,
    artificial_delay: float = 0.0,
) -> FileStats:
    """Прочитать файл и вернуть его статистику."""
    
    # 1. Прочитать path в кодировке UTF-8.
    text = path.read_text(encoding="utf-8")
    
    # 2. Выполнить паузу если artificial_delay больше нуля.
    if artificial_delay > 0.0:
        time.sleep(artificial_delay)
        
    # 3. Создать и вернуть FileStats.
    return FileStats(
        file_name=path.name,
        lines=len(text.splitlines()),
        words=len(text.split()),
        characters=len(text)
    )


def main() -> int:
    """Обработать аргументы и вывести результат в JSON."""
    
    # 4. Проверить количество аргументов sys.argv.
    if len(sys.argv) not in (2, 3):
        print("Ошибка: Обязательный формат: python worker.py ПУТЬ_К_ФАЙЛУ [ЗАДЕРЖКА]", file=sys.stderr)
        return 1

    # 5. Преобразовать путь в Path и задержку во float.
    try:
        path = Path(sys.argv[1])
        delay = float(sys.argv[2]) if len(sys.argv) == 3 else 0.0
    except ValueError:
        print("Ошибка: Задержка должна быть числом.", file=sys.stderr)
        return 1

    # 6. Проверить существование обычного файла.
    if not path.is_file():
        print(f"Ошибка: Файл '{path}' не существует или не является файлом.", file=sys.stderr)
        return 1

    # 7. Вызвать analyze_file.
    try:
        result = analyze_file(path, delay)
        # 8. Вывести json.dumps(asdict(result), ensure_ascii=False).
        print(json.dumps(asdict(result), ensure_ascii=False))
        # 9. Вернуть 0 при успехе.
        return 0
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())