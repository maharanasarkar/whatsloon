import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "whatsloon",
    level: int = logging.INFO,
    log_file: str = "logs/application.log",
) -> logging.Logger:
    """
    Set up a logger with a specified name, logging level, and log file.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING, etc.).
        log_file (str): The file to which the logs will be written.

    Returns:
        logging.Logger: Configured logger instance.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=2
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()