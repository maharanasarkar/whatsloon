from .logger.default_logger import setup_logger
import logging


def configure_logging(
    level: int = logging.INFO, log_file: str = "logs/application.log"
):
    """
    Configure the logging for the application.

    Args:
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING, etc.).
        log_file (str): The file to which the logs will be written.
    """

    setup_logger(level=level, log_file=log_file)
