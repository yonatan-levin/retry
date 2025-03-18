"""
Logging utilities for the retry package.

This module provides logging functionality for the retry package,
including a custom formatter and convenience functions.
"""

import logging
import sys
import time
import os
from typing import Optional, Dict, Any

# Default logging level
DEFAULT_LEVEL = logging.INFO

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default date format
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Cache for loggers to avoid creating multiple loggers for the same name
_loggers: Dict[str, logging.Logger] = {}


class ColoredFormatter(logging.Formatter):
    """
    A formatter that adds colors to log messages.
    """
    
    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def __init__(self, fmt: str = DEFAULT_FORMAT, datefmt: str = DEFAULT_DATE_FORMAT, use_colors: bool = True):
        """
        Initialize a ColoredFormatter.
        
        Args:
            fmt: Log format string
            datefmt: Date format string
            use_colors: Whether to use colors in log messages
        """
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        log_message = super().format(record)
        
        if self.use_colors and record.levelno in self.COLORS:
            log_message = f"{self.COLORS[record.levelno]}{log_message}{self.RESET}"
        
        return log_message


def get_logger(name: str, level: Optional[int] = None, use_colors: bool = True) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        level: Logging level (defaults to DEFAULT_LEVEL)
        use_colors: Whether to use colors in log messages
        
    Returns:
        Logger instance
    """
    # Check if logger already exists
    if name in _loggers:
        return _loggers[name]
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Set level
    logger.setLevel(level or DEFAULT_LEVEL)
    
    # Only add handlers if none exist
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level or DEFAULT_LEVEL)
        
        # Create formatter
        formatter = ColoredFormatter(use_colors=use_colors)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    # Cache logger
    _loggers[name] = logger
    
    return logger


def setup_file_logging(log_dir: str, name: str = "retry") -> None:
    """
    Set up file logging.
    
    Args:
        log_dir: Directory to store log files
        name: Logger name
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get logger
    logger = get_logger(name)
    
    # Create file handler
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    logger.info(f"Logging to file: {log_file}")


def set_log_level(level: int, name: Optional[str] = None) -> None:
    """
    Set the logging level.
    
    Args:
        level: Logging level
        name: Logger name (None for all loggers)
    """
    if name:
        # Set level for specific logger
        if name in _loggers:
            _loggers[name].setLevel(level)
            for handler in _loggers[name].handlers:
                handler.setLevel(level)
    else:
        # Set level for all loggers
        for logger in _loggers.values():
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level) 