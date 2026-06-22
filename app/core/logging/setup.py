import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

LOG_THEME = Theme(
    {
        "logging.level.debug": "dim cyan",
        "logging.level.info": "green",
        "logging.level.warning": "yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold white on red",
    }
)

_console = Console(theme=LOG_THEME)
_configured = False


def setup_logging(*, level: int = logging.INFO, log_dir: str = "logs") -> None:
    global _configured
    if _configured:
        return

    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        console_handler = RichHandler(
            console=_console,
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_level=True,
            show_path=False,
        )
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(console_handler)

        file_handler = logging.FileHandler(
            log_path / "mailpulse.log",
            mode="a",
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
