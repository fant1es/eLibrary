import logging
import os
from logging.handlers import RotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

_LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "server") -> logging.Logger:
    """
    Возвращает настроенный логгер с двумя обработчиками:
      - консоль (INFO и выше)
      - файл logs/server.log с ротацией (DEBUG и выше)
    """
    logger = logging.getLogger(name)

    # Повторный вызов не добавляет хендлеры дважды
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # --- Консоль ---------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # --- Файл с ротацией: 5 МБ * 3 файла ---
    file_handler = RotatingFileHandler(
        filename=os.path.join(LOGS_DIR, "server.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


class ClientLoggerAdapter(logging.LoggerAdapter):
    """Добавляет контекст клиента [addr (username)] к каждому сообщению"""
    def __init__(self, logger: logging.Logger, address: tuple, ctx):
        super().__init__(logger, {})
        self._address = address
        self._ctx = ctx

    def process(self, msg, kwargs):
        addr_str = f"{self._address[0]}:{self._address[1]}"
        user_str = self._ctx.username or "Гость"
        return f"[{addr_str} ({user_str})] {msg}", kwargs