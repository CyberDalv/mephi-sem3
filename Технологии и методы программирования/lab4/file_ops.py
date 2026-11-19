from __future__ import annotations
import shutil
from pathlib import Path

class FileManagerCore:
    def __init__(self, root: Path) -> None:
        if root.is_symlink() or (root.exists() and not root.is_dir()):
            raise ValueError("Root должен быть обычным каталогом, а не ссылкой.")
        
        self.root = root.resolve()
        self.current_dir = self.root

    def display_path(self, path: Path) -> str:
        """Вернуть путь вида / или /inbox/file.txt."""
        if path == self.root:
            return "/"
        try:
            rel = path.relative_to(self.root)
            return "/" + rel.as_posix()
        except ValueError:
            raise ValueError("Путь выходит за пределы workspace")

    def resolve_user_path(
        self,
        raw: str,
        *,
        must_exist: bool = False,
    ) -> Path:
        """Разрешить путь внутри root; ссылки не поддерживаются."""
        if not raw:
            raise ValueError("Путь не может быть пустым")
        if "\\" in raw:
            raise ValueError("Символ обратной косой черты запрещен")
        if ":" in raw:
            raise ValueError("Буквы дисков запрещены")

        if raw.startswith("/"):
            candidate = self.root / raw.lstrip("/")
        else:
            candidate = self.current_dir / raw

        current = candidate
        while current != current.parent:
            if current.is_symlink():
                raise ValueError("Символические ссылки запрещены")
            current = current.parent

        candidate = candidate.resolve(strict=False)

        if candidate != self.root and not candidate.is_relative_to(self.root):
            raise ValueError("Путь выходит за пределы workspace")

        if must_exist and not candidate.exists():
            raise ValueError(f"Объект не существует: {raw}")

        return candidate

    def list_entries(self, raw: str | None = None) -> list[tuple[str, str]]:
        target = self.current_dir if not raw else self.resolve_user_path(raw, must_exist=True)
        
        if not target.is_dir():
            raise ValueError("Указанный путь не является каталогом")
            
        entries = []
        for entry in target.iterdir():
            if entry.is_symlink():
                raise ValueError("Обнаружена символическая ссылка внутри каталога")
            entry_type = "DIR" if entry.is_dir() else "FILE"
            entries.append((entry_type, entry.name))
            
        return sorted(entries, key=lambda x: x[1])

    def change_directory(self, raw: str) -> Path:
        target = self.resolve_user_path(raw, must_exist=True)
        if not target.is_dir():
            raise ValueError("Цель не является каталогом")
        self.current_dir = target
        return target

    def _check_no_symlinks_in_tree(self, path: Path) -> None:
        if path.is_symlink():
            raise ValueError("Символические ссылки запрещены")
        if path.is_dir():
            for item in path.rglob('*'):
                if item.is_symlink():
                    raise ValueError("Символические ссылки запрещены внутри дерева")

    def copy_entry(self, source: str, destination: str) -> Path:
        src_path = self.resolve_user_path(source, must_exist=True)
        dst_path = self.resolve_user_path(destination, must_exist=False)

        if dst_path.exists():
            raise ValueError("Назначение уже существует")
        if not dst_path.parent.exists() or not dst_path.parent.is_dir():
            raise ValueError("Родительский каталог назначения не существует или не является каталогом")
            
        self._check_no_symlinks_in_tree(src_path)

        if dst_path.is_relative_to(src_path):
            raise ValueError("Нельзя копировать каталог внутрь самого себя")

        if src_path.is_dir():
            shutil.copytree(src_path, dst_path, symlinks=False)
        else:
            shutil.copy2(src_path, dst_path)

        return dst_path

    def move_entry(self, source: str, destination: str) -> Path:
        src_path = self.resolve_user_path(source, must_exist=True)
        dst_path = self.resolve_user_path(destination, must_exist=False)

        if src_path == self.root:
            raise ValueError("Нельзя переместить корневой каталог")
        if self.current_dir.is_relative_to(src_path):
            raise ValueError("Нельзя перемещать текущий каталог или его предка")
            
        if dst_path.exists():
            raise ValueError("Назначение уже существует")
        if not dst_path.parent.exists() or not dst_path.parent.is_dir():
            raise ValueError("Родительский каталог назначения не существует или не является каталогом")

        self._check_no_symlinks_in_tree(src_path)

        if dst_path.is_relative_to(src_path):
            raise ValueError("Нельзя перемещать каталог внутрь самого себя")

        shutil.move(src_path, dst_path)
        return dst_path

    def remove_entry(self, raw: str) -> Path:
        target = self.resolve_user_path(raw, must_exist=True)
        if target.is_symlink():
            raise ValueError("Символические ссылки запрещены")
        if target.is_dir():
            raise ValueError("Удаление каталогов запрещено, только обычные файлы")

        target.unlink()
        return target