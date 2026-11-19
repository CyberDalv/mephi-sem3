from __future__ import annotations
from pathlib import Path

from file_ops import FileManagerCore
from shell import FileManagerShell

ROOT_DIR: Path = Path(__file__).resolve().parent
WORKSPACE_DIR: Path = ROOT_DIR / "workspace"

def prepare_workspace() -> None:
    """Создать учебное дерево без перезаписи данных."""
    directories = [
        WORKSPACE_DIR,
        WORKSPACE_DIR / "inbox",
        WORKSPACE_DIR / "archive"
    ]
    
    for d in directories:
        if d.exists():
            if d.is_symlink():
                raise ValueError(f"Путь {d.name} является ссылкой, а не обычным каталогом")
            if not d.is_dir():
                raise ValueError(f"Путь {d.name} существует, но не является каталогом")
        else:
            d.mkdir(parents=True, exist_ok=True)

    inbox = WORKSPACE_DIR / "inbox"
    alpha = inbox / "alpha.txt"
    beta = inbox / "beta.txt"

    if not alpha.exists():
        alpha.write_text("alpha", encoding="utf-8")
    if not beta.exists():
        beta.write_text("beta", encoding="utf-8")

def main() -> int:
    try:
        prepare_workspace()
        core = FileManagerCore(WORKSPACE_DIR)
        shell = FileManagerShell(core)
        shell.cmdloop()
        return 0
    except Exception as e:
        print(f"Критическая ошибка запуска: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())