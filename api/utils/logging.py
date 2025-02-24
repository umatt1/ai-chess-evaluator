"""Logging configuration for the chess application."""

import logging
import sys
from typing import Optional

def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Set up a logger with consistent formatting.
    
    Args:
        name: Name of the logger
        level: Optional logging level (defaults to INFO)
        
    Returns:
        logging.Logger: Configured logger
    """
    if level is None:
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Create default logger
logger = setup_logger('chess_app')
