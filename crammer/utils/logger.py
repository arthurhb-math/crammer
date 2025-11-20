import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str = "crammer",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "crammer") -> logging.Logger:
    return logging.getLogger(name)


class LogCapture:
    def __init__(self, logger_name: str = "crammer", level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.handler = logging.handlers.MemoryHandler(capacity=1000)
        self.messages = []

    def __enter__(self):
        logger = logging.getLogger(self.logger_name)
        self.handler.setLevel(self.level)
        logger.addHandler(self.handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self.handler)
        self.messages = [record.getMessage() for record in self.handler.buffer]

    def get_messages(self):
        return self.messages
