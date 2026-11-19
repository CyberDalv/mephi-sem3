from __future__ import annotations
import cmd
import shlex
from file_ops import FileManagerCore

class FileManagerShell(cmd.Cmd):
    intro = "Учебный файловый менеджер. Введите help."

    def __init__(self, core: FileManagerCore) -> None:
        super().__init__()
        self.core = core
        self.update_prompt()

    def update_prompt(self) -> None:
        self.prompt = f"fm:{self.core.display_path(self.core.current_dir)}> "

    def split_args(self, raw: str, expected: int | tuple[int, ...]) -> list[str]:
        if "\\" in raw:
            raise ValueError("Символ обратной косой черты запрещен")
            
        try:
            args = shlex.split(raw, posix=True)
        except ValueError as e:
            raise ValueError(f"Ошибка разбора аргументов: {e}")

        if isinstance(expected, int):
            expected = (expected,)

        if len(args) not in expected:
            raise ValueError(f"Неверное количество аргументов. Ожидалось: {expected}, получено: {len(args)}")
            
        return args

    def emptyline(self) -> None:
        """Не повторять предыдущую команду при пустом вводе."""
        return None

    def do_pwd(self, arg: str) -> None:
        """pwd: показать текущий каталог менеджера."""
        try:
            self.split_args(arg, 0)
            print(self.core.display_path(self.core.current_dir))
        except (ValueError, OSError) as e:
            print(f"ERROR pwd: {e}")

    def do_ls(self, arg: str) -> None:
        """ls [ПУТЬ]: показать содержимое каталога."""
        try:
            args = self.split_args(arg, (0, 1))
            target = args[0] if args else None
            entries = self.core.list_entries(target)
            for etype, ename in entries:
                print(f"{etype}\t{ename}")
        except (ValueError, OSError) as e:
            print(f"ERROR ls: {e}")

    def do_cd(self, arg: str) -> None:
        """cd ПУТЬ: изменить текущий каталог менеджера."""
        try:
            args = self.split_args(arg, 1)
            target = self.core.change_directory(args[0])
            self.update_prompt()
            print(f"OK cd {self.core.display_path(target)}")
        except (ValueError, OSError) as e:
            print(f"ERROR cd: {e}")

    def do_cp(self, arg: str) -> None:
        """cp ИСТОЧНИК НАЗНАЧЕНИЕ: скопировать объект."""
        try:
            args = self.split_args(arg, 2)
            src_disp = self.core.display_path(self.core.resolve_user_path(args[0]))
            dest = self.core.copy_entry(args[0], args[1])
            dst_disp = self.core.display_path(dest)
            print(f"OK cp {src_disp} -> {dst_disp}")
        except (ValueError, OSError) as e:
            print(f"ERROR cp: {e}")

    def do_mv(self, arg: str) -> None:
        """mv ИСТОЧНИК НАЗНАЧЕНИЕ: переместить объект."""
        try:
            args = self.split_args(arg, 2)
            src_disp = self.core.display_path(self.core.resolve_user_path(args[0]))
            dest = self.core.move_entry(args[0], args[1])
            dst_disp = self.core.display_path(dest)
            print(f"OK mv {src_disp} -> {dst_disp}")
        except (ValueError, OSError) as e:
            print(f"ERROR mv: {e}")

    def do_rm(self, arg: str) -> None:
        """rm ПУТЬ: удалить обычный файл."""
        try:
            args = self.split_args(arg, 1)
            target = self.core.resolve_user_path(args[0])
            disp = self.core.display_path(target)
            self.core.remove_entry(args[0])
            print(f"OK rm {disp}")
        except (ValueError, OSError) as e:
            print(f"ERROR rm: {e}")

    def do_exit(self, arg: str) -> bool:
        """exit: завершить программу."""
        try:
            self.split_args(arg, 0)
            return True
        except (ValueError, OSError) as e:
            print(f"ERROR exit: {e}")
            return False

    def do_EOF(self, arg: str) -> bool:
        """EOF: завершить программу по концу ввода."""
        print()
        return True