from __future__ import annotations

import io
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


def configure_utf8_output() -> None:
    """Включить вывод в UTF-8 независимо от настроек консоли платформы."""

    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


def analyze_file(
    path: Path,
    artificial_delay: float = 0.0,
) -> FileStats:
    """Прочитать файл и вернуть его статистику."""

    # 1. Чтение файла в явной кодировке UTF-8.
    text: str = path.read_text(encoding="utf-8")

    # 2. Искусственная задержка, имитирующая ожидание ввода-вывода.
    if artificial_delay > 0:
        time.sleep(artificial_delay)

    # 3. Подсчёт статистики по заданным правилам.
    return FileStats(
        file_name=path.name,
        lines=len(text.splitlines()),
        words=len(text.split()),
        characters=len(text),
    )


def main() -> int:
    """Обработать аргументы и вывести результат в JSON."""

    configure_utf8_output()

    # 4. Проверка количества аргументов.
    # Формат: python worker.py ПУТЬ_К_ФАЙЛУ [ЗАДЕРЖКА]
    if len(sys.argv) not in (2, 3):
        print(
            "Использование: python worker.py ПУТЬ_К_ФАЙЛУ [ЗАДЕРЖКА]",
            file=sys.stderr,
        )
        return 2

    # 5. Преобразование аргументов в Path и float.
    path: Path = Path(sys.argv[1])
    delay: float = 0.0
    if len(sys.argv) == 3:
        try:
            delay = float(sys.argv[2])
        except ValueError:
            print(
                f"Ошибка: задержка должна быть числом, получено {sys.argv[2]!r}",
                file=sys.stderr,
            )
            return 2
        if delay < 0:
            print("Ошибка: задержка не может быть отрицательной", file=sys.stderr)
            return 2

    # 6. Проверка существования обычного файла.
    if not path.is_file():
        print(f"Ошибка: файл не найден: {path}", file=sys.stderr)
        return 1

    # 7. Анализ файла.
    try:
        result: FileStats = analyze_file(path, delay)
    except (OSError, UnicodeDecodeError) as error:
        print(f"Ошибка чтения файла: {error}", file=sys.stderr)
        return 1

    # 8. Единственная JSON-строка в stdout.
    print(json.dumps(asdict(result), ensure_ascii=False))

    # 9. Успех.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())