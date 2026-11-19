# Добавить в импорты:
from colorama import just_fix_windows_console
from access_rights import (
    read_snapshot, owner_group_labels, format_access,
    parse_change, transform_mode
)
import shlex

def do_color(self, arg: str) -> None:
    """color on|off: переключить цвет."""
    val = arg.strip().lower()
    if val == 'on':
        self.use_color = True
    elif val == 'off':
        self.use_color = False
    else:
        print("ERROR color: укажите on или off")

def do_stat(self, arg: str) -> None:
    """stat ПУТЬ: показать права и владельца."""
    try:
        args = shlex.split(arg)
        if not args:
            raise ValueError("Укажите путь")
        # предполагается наличие self._resolve(path) из лаб 3
        path = self._resolve(args[0]) 
        if not path.exists(follow_symlinks=False):
            raise OSError(f"Объект не найден: {args[0]}")
        
        snapshot = read_snapshot(path)
        if snapshot.is_symlink:
            raise ValueError("Символические ссылки не поддерживаются")
            
        owner, group = owner_group_labels(snapshot)
        print(f"Владелец: {owner}\nГруппа: {group}")
        print(f"Права: {format_access(snapshot, self.use_color)}")
    except (ValueError, OSError) as e:
        print(f"ERROR stat: {e}")

def do_chmod(self, arg: str) -> None:
    """chmod ИЗМЕНЕНИЕ ПУТЬ: изменить права."""
    try:
        args = shlex.split(arg)
        if len(args) != 2:
            raise ValueError("Требуется выражение и путь")
        expr, path_str = args
        
        path = self._resolve(path_str)
        if not path.exists(follow_symlinks=False):
            raise OSError(f"Файл не найден: {path_str}")
            
        snapshot = read_snapshot(path)
        if snapshot.is_symlink:
            raise ValueError("Символические ссылки не поддерживаются")
        if not path.is_file():
            raise ValueError("Изменение прав поддерживается только для файлов")

        change = parse_change(expr)
        old_access = format_access(snapshot, self.use_color)
        
        new_mode = transform_mode(snapshot.mode, change)
        from dataclasses import replace
        new_snapshot = replace(snapshot, mode=new_mode)
        new_access = format_access(new_snapshot, self.use_color)
        
        print(f"Файл: {path_str}")
        print(f"Было:  {old_access}")
        print(f"Будет: {new_access}")
        print(f"Изменение: {expr}")
        ans = input("Применить? [y/N] ").strip()
        
        if ans == 'y':
            path.chmod(new_mode)
            final_snapshot = read_snapshot(path)
            print(f"Фактически: {format_access(final_snapshot, self.use_color)}")
        else:
            print("Отменено")
    except (ValueError, OSError) as e:
        print(f"ERROR chmod: {e}")