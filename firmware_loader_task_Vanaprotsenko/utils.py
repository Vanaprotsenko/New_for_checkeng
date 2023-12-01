from __future__ import annotations


def print_with_color(msg: str, color: str = '0') -> None:
    print(f'\033[{color}m{msg}\033[0m')
