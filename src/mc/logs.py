import logging
import os
from logging.handlers import RotatingFileHandler

from mc.config import MC_HOME

LOG_FORMAT1 = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_FORMAT2 = "%(asctime)s - %(levelname)s - %(message)s"

formatter = logging.Formatter(LOG_FORMAT1)


def get_console_log_handler():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    return console_handler


def get_file_log_handler(name):
    os.makedirs(f"{MC_HOME}/logs", exist_ok=True)
    file_handler = logging.FileHandler(f"{MC_HOME}/logs/{name}.log")
    file_handler.setFormatter(formatter)
    return file_handler


def get_rotating_file_log_handler(name):
    os.makedirs(f"{MC_HOME}/logs", exist_ok=True)
    rotating_file_handler = RotatingFileHandler(
        f"{MC_HOME}/logs/{name}.log",
        maxBytes=10_000_000,  # 10 MB
        backupCount=10,  # keep 10 old files
    )
    rotating_file_handler.setFormatter(formatter)
    return rotating_file_handler
