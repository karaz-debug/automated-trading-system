# utils/logger.py

import logging
import os

def get_logger(name: str, log_file: str = 'logs/trading_system.log', level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and log file.

    :param name: Logger name
    :param log_file: Log file path
    :param level: Logging level
    :return: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers to the logger
    if not logger.handlers:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
