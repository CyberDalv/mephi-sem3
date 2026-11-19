from __future__ import annotations

from dataclasses import dataclass
from math import isqrt

CHECKSUM_MODULUS: int = 1_000_000_007


@dataclass(frozen=True, slots=True)
class PrimeStats:
    count: int
    max_prime: int | None
    checksum: int


def is_prime(number: int) -> bool:
    """Вернуть True только для простого числа."""
    # 1 Обработать числа меньше 2.
    if number < 2:
        return False
    # 2 Проверить делители не дальше isqrt(number).
    for i in range(2, isqrt(number) + 1):
        if number % i == 0:
            return False
    return True


def analyze_range(bounds: tuple[int, int]) -> PrimeStats:
    """Проанализировать обе границы включительно."""
    start, stop = bounds
    # 3 Проверить корректность границ.
    if start > stop or start < 0:
        raise ValueError("Некорректные границы диапазона")

    # 4 Посчитать count, max_prime и checksum.
    count: int = 0
    max_prime: int | None = None
    checksum: int = 0

    for i in range(start, stop + 1):
        if is_prime(i):
            count += 1
            max_prime = i
            checksum = (checksum + i) % CHECKSUM_MODULUS
            
    # 5 Применить CHECKSUM_MODULUS к итоговой сумме.
    return PrimeStats(count, max_prime, checksum)


def merge_stats(items: list[PrimeStats]) -> PrimeStats:
    """Объединить непересекающиеся частичные результаты."""
    # 6 Обработать пустой список.
    if not items:
        return PrimeStats(0, None, 0)

    # 7 Сложить count и checksum, выбрать общий максимум.
    total_count: int = 0
    total_checksum: int = 0
    global_max: int | None = None

    for item in items:
        total_count += item.count
        total_checksum = (total_checksum + item.checksum) % CHECKSUM_MODULUS
        if item.max_prime is not None:
            if global_max is None or item.max_prime > global_max:
                global_max = item.max_prime

    return PrimeStats(total_count, global_max, total_checksum)