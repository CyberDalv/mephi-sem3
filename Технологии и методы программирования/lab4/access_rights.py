from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import stat
from colorama import Fore, Style
import sys

try:
    import pwd
    import grp
except ImportError:
    pwd = None
    grp = None

@dataclass(frozen=True)
class AccessSnapshot:
    mode: int
    uid: int | None
    gid: int | None
    is_symlink: bool

def permission_triples(mode: int) -> tuple[int, int, int]:
    value = stat.S_IMODE(mode)
    return ((value >> 6) & 7, (value >> 3) & 7, value & 7)

TRIPLE_COLORS = {
    0: Fore.RESET,   1: Fore.BLUE,
    2: Fore.GREEN,   3: Fore.CYAN,
    4: Fore.RED,     5: Fore.MAGENTA,
    6: Fore.YELLOW,  7: Fore.WHITE,
}

def paint(label: str, bits: int, use_color: bool) -> str:
    if not use_color:
        return label
    return TRIPLE_COLORS[bits] + label + Style.RESET_ALL

def read_snapshot(path: Path) -> AccessSnapshot:
    st = path.lstat()
    return AccessSnapshot(
        mode=st.st_mode,
        uid=st.st_uid,
        gid=st.st_gid,
        is_symlink=stat.S_ISLNK(st.st_mode)
    )

def owner_group_labels(snapshot: AccessSnapshot) -> tuple[str, str]:
    uid_str = str(snapshot.uid) if snapshot.uid is not None else "None"
    gid_str = str(snapshot.gid) if snapshot.gid is not None else "None"

    owner = uid_str
    group = gid_str

    if pwd and snapshot.uid is not None:
        try:
            owner = f"{pwd.getpwuid(snapshot.uid).pw_name} ({uid_str})"
        except KeyError:
            pass
    if grp and snapshot.gid is not None:
        try:
            group = f"{grp.getgrgid(snapshot.gid).gr_name} ({gid_str})"
        except KeyError:
            pass

    return owner, group

def _bits_to_rwx(bits: int) -> str:
    r = 'r' if bits & 4 else '-'
    w = 'w' if bits & 2 else '-'
    x = 'x' if bits & 1 else '-'
    return r + w + x

def format_access(snapshot: AccessSnapshot, use_color: bool) -> str:
    file_mode = stat.filemode(snapshot.mode)
    octal_mode = oct(stat.S_IMODE(snapshot.mode))
    u, g, o = permission_triples(snapshot.mode)

    u_str = paint(f"U={_bits_to_rwx(u)}", u, use_color)
    g_str = paint(f"G={_bits_to_rwx(g)}", g, use_color)
    o_str = paint(f"O={_bits_to_rwx(o)}", o, use_color)

    return f"{file_mode} {octal_mode:>6} {u_str} {g_str} {o_str}"

def parse_change(expr: str) -> tuple[str, str, int]:
    if len(expr) < 3:
        raise ValueError("Слишком короткое выражение")
    
    target, op, perms = expr[0], expr[1], expr[2:]
    
    if target not in ('u', 'g', 'o'):
        raise ValueError(f"Класс {target} не поддерживается")
    if op not in ('+', '-', '='):
        raise ValueError(f"Операция {op} не поддерживается")
        
    mask = 0
    seen = set()
    for p in perms:
        if p in seen:
            raise ValueError("Повтор разрешения запрещён")
        seen.add(p)
        if p == 'r': mask |= 4
        elif p == 'w': mask |= 2
        elif p == 'x': mask |= 1
        else: raise ValueError(f"Неизвестное разрешение: {p}")
        
    return target, op, mask

def transform_mode(current: int, change: tuple[str, str, int]) -> int:
    target, op, mask = change
    shift = {'u': 6, 'g': 3, 'o': 0}[target]
    target_mask = mask << shift

    if op == '+':
        new_mode = current | target_mask
    elif op == '-':
        new_mode = current & ~target_mask
    elif op == '=':
        clear_mask = ~(7 << shift)
        new_mode = (current & clear_mask) | target_mask
    
    return new_mode