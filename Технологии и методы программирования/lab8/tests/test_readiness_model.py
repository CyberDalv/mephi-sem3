from __future__ import annotations
import queue
import pytest

def test_queue_observation_vs_consumption():
    q = queue.Queue()
    q.put("item1")
    
    # M1. Фиксируем наблюдение "не пуста"
    assert not q.empty()
    
    # Извлекаем элемент
    val = q.get()
    q.task_done()
    assert val == "item1"
    
    # Следующий get_nowait вызывает queue.Empty (состояние изменилось)
    with pytest.raises(queue.Empty):
        q.get_nowait()

def test_queue_timeout_and_stop_signal():
    q = queue.Queue()
    
    # M2. get с таймаутом вызывает queue.Empty для пустой очереди
    with pytest.raises(queue.Empty):
        q.get(timeout=0.01)
        
    # После этого в неё можно положить и получить данные
    q.put("data")
    assert q.get() == "data"
    q.task_done()
    
    # Проверка сигнала STOP
    STOP = object()
    q.put(STOP)
    item = q.get()
    assert item is STOP
    q.task_done()
