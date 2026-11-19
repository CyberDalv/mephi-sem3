from __future__ import annotations
import shutil
from pathlib import Path
from errors import WorkspaceViolationError, OperationRejectedError

class FileManagerCore:
    def __init__(self) -> None:
        self.workspace = Path("workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.current_dir = self.workspace

    def resolve_path(self, path_str: str, must_exist: bool = False) -> Path:
        try:
            path = (self.current_dir / path_str).resolve()
        except Exception as e:
            raise WorkspaceViolationError(f"Некорректный путь: {path_str}") from e

        if not str(path).startswith(str(self.workspace)):
            raise WorkspaceViolationError(f"Путь выходит за пределы workspace: {path_str}")
        
        if must_exist and not path.exists():
            raise FileNotFoundError(f"Объект не найден: {path_str}")
        return path

    def cmd_pwd(self) -> str:
        rel_path = self.current_dir.relative_to(self.workspace)
        return f"/{rel_path}" if str(rel_path) != "." else "/"

    def cmd_ls(self, path_str: str | None = None) -> list[str]:
        target = self.resolve_path(path_str, must_exist=True) if path_str else self.current_dir
        if not target.is_dir():
            raise NotADirectoryError(f"Не является каталогом: {path_str}")
        return [item.name for item in target.iterdir()]

    def cmd_cd(self, path_str: str) -> str:
        target = self.resolve_path(path_str, must_exist=True)
        if not target.is_dir():
            raise NotADirectoryError(f"Цель не является каталогом: {path_str}")
        # Присваивание нового каталога выполняется только после успешных проверок
        self.current_dir = target
        return f"Переход в {path_str}"

    def cmd_cp(self, src_str: str, dst_str: str) -> str:
        src = self.resolve_path(src_str, must_exist=True)
        dst = self.resolve_path(dst_str, must_exist=False)

        if not src.is_file():
            raise IsADirectoryError(f"Источник не является обычным файлом: {src_str}")
        if dst.exists():
            raise FileExistsError(f"Назначение уже существует: {dst_str}")
        
        shutil.copy2(src, dst)
        return f"Скопировано {src_str} в {dst_str}"

    def cmd_mv(self, src_str: str, dst_str: str) -> str:
        src = self.resolve_path(src_str, must_exist=True)
        dst = self.resolve_path(dst_str, must_exist=False)

        if src == self.workspace or src in self.workspace.parents:
            raise OperationRejectedError("Запрещено перемещать корень workspace или его предков")
        if dst == src or src in dst.parents:
            raise OperationRejectedError("Запрещено переносить каталог внутрь самого себя")
        if dst.exists():
            raise FileExistsError(f"Назначение уже существует: {dst_str}")

        shutil.move(src, dst)
        return f"Перемещено {src_str} в {dst_str}"

    def cmd_rm(self, path_str: str) -> str:
        path = self.resolve_path(path_str, must_exist=True)
        
        if path == self.workspace or path in self.workspace.parents:
            raise OperationRejectedError("Запрещено удалять корень workspace или рабочую область")
        if path.is_dir():
            raise IsADirectoryError(f"Удаление каталогов через rm запрещено: {path_str}")
        
        path.unlink()
        return f"Удален файл {path_str}"