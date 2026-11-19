from __future__ import annotations

class FileManagerError(Exception):
    """Ожидаемый отказ по правилам менеджера."""
    pass

class WorkspaceViolationError(FileManagerError):
    """Недопустимый путь или выход за рабочую область."""
    pass

class OperationRejectedError(FileManagerError):
    """Операция запрещена правилами менеджера."""
    pass
