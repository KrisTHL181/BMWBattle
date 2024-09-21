from sys import stderr as stdout
import time
import colorama

colorama.just_fix_windows_console()


def info(message: str) -> None:
    stdout.write(
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {colorama.Fore.LIGHTYELLOW_EX}[GAME]: {colorama.Fore.LIGHTWHITE_EX}{message}{colorama.Fore.RESET}\n"
    )
