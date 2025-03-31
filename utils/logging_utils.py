import logging
import sys
from typing import Dict, Any, Optional


def setup_logger(
    name: str = None,
    level: int = logging.INFO,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Set up and configure logger"""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_webhook_request(logger: logging.Logger, request_data: Dict[str, Any]) -> None:
    """Log webhook request with sensitive data redacted"""
    # Create a copy to avoid modifying the original
    safe_data = (
        request_data.copy()
        if isinstance(request_data, dict)
        else {"data": str(request_data)}
    )

    logger.info(f"Webhook request: {safe_data}")