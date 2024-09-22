from sys import stdout, stderr
import time
import colorama

colorama.just_fix_windows_console()


def info(message: str) -> None:
    stdout.write(
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {colorama.Fore.LIGHTYELLOW_EX}[GAME]: {colorama.Fore.LIGHTWHITE_EX}{message}{colorama.Fore.RESET}\n"
    )


def log(message: str) -> None:
    stderr.write(
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {colorama.Fore.LIGHTYELLOW_EX}[INFO]: {colorama.Fore.LIGHTCYAN_EX}{message}{colorama.Fore.RESET}\n"
    )


def is_redirected() -> bool:
    return not stdout.isatty()
