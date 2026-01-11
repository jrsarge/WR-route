"""Logging configuration for Fast Food Route Optimizer.

This module provides structured logging with support for console and file output,
performance tracking, and context-aware logging.
"""

import functools
import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# Default logging format
LOGGING_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Detailed format for file logging
FILE_LOGGING_FORMAT = (
    "%(asctime)s [%(levelname)8s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """Set up logging configuration for the application.

    Configures both console and optional file logging with appropriate
    formatting and log levels.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs to file
        console: If True, also log to console (default: True)

    Example:
        >>> setup_logging(level="DEBUG", log_file="./logs/app.log")
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            LOGGING_FORMAT,
            datefmt=LOGGING_DATE_FORMAT,
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            FILE_LOGGING_FORMAT,
            datefmt=LOGGING_DATE_FORMAT,
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googlemaps").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


def log_performance(func: F) -> F:
    """Decorator to log function execution time.

    Logs the time taken by a function to execute, useful for tracking
    performance of critical operations like optimization and API calls.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that logs execution time

    Example:
        >>> @log_performance
        ... def optimize_route(restaurants):
        ...     # optimization logic
        ...     pass
    """
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        logger.debug(f"Starting {func.__name__}")

        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            logger.info(
                f"Completed {func.__name__} in {elapsed_time:.2f}s",
                extra={
                    "function": func.__name__,
                    "duration_seconds": elapsed_time,
                },
            )
            return result

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Failed {func.__name__} after {elapsed_time:.2f}s: {e}",
                extra={
                    "function": func.__name__,
                    "duration_seconds": elapsed_time,
                    "error": str(e),
                },
            )
            raise

    return cast(F, wrapper)


def log_api_call(func: F) -> F:
    """Decorator to log API calls without exposing sensitive data.

    Logs API calls with sanitized parameters (API keys removed) for
    debugging and monitoring purposes.

    Args:
        func: API function to decorate

    Returns:
        Decorated function that logs API calls safely

    Example:
        >>> @log_api_call
        ... def search_restaurants(self, location, radius):
        ...     # API call logic
        ...     pass
    """
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Sanitize kwargs by removing sensitive data
        safe_kwargs = {
            k: "***REDACTED***" if "key" in k.lower() or "token" in k.lower() else v
            for k, v in kwargs.items()
        }

        logger.debug(
            f"API call: {func.__name__}",
            extra={
                "function": func.__name__,
                "kwargs": safe_kwargs,
            },
        )

        try:
            result = func(*args, **kwargs)
            logger.debug(f"API call successful: {func.__name__}")
            return result

        except Exception as e:
            logger.error(
                f"API call failed: {func.__name__}: {e}",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                },
            )
            raise

    return cast(F, wrapper)


class ProgressLogger:
    """Context manager for logging progress of long-running operations.

    Provides a simple way to log progress updates during operations like
    data collection, optimization, and batch processing.

    Example:
        >>> with ProgressLogger("Collecting restaurants", total=100) as progress:
        ...     for i in range(100):
        ...         # do work
        ...         progress.update(i + 1)
    """

    def __init__(
        self,
        operation: str,
        total: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize progress logger.

        Args:
            operation: Description of the operation being tracked
            total: Optional total number of items to process
            logger: Optional logger instance (uses root logger if None)
        """
        self.operation = operation
        self.total = total
        self.logger = logger or logging.getLogger()
        self.current = 0
        self.start_time = 0.0

    def __enter__(self) -> "ProgressLogger":
        """Enter context and log operation start."""
        self.start_time = time.time()
        if self.total:
            self.logger.info(f"Starting {self.operation} (0/{self.total})")
        else:
            self.logger.info(f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and log operation completion or failure."""
        elapsed_time = time.time() - self.start_time

        if exc_type is None:
            if self.total:
                self.logger.info(
                    f"Completed {self.operation} ({self.current}/{self.total}) "
                    f"in {elapsed_time:.2f}s"
                )
            else:
                self.logger.info(
                    f"Completed {self.operation} in {elapsed_time:.2f}s"
                )
        else:
            self.logger.error(
                f"Failed {self.operation} after {elapsed_time:.2f}s: {exc_val}"
            )

    def update(self, current: int, message: Optional[str] = None) -> None:
        """Update progress and log if significant change.

        Args:
            current: Current progress count
            message: Optional additional message to log
        """
        self.current = current

        # Log every 10% progress if total is known
        if self.total and current % max(1, self.total // 10) == 0:
            percentage = (current / self.total) * 100
            elapsed_time = time.time() - self.start_time

            log_msg = f"{self.operation}: {current}/{self.total} ({percentage:.1f}%)"
            if message:
                log_msg += f" - {message}"

            self.logger.info(
                log_msg,
                extra={
                    "operation": self.operation,
                    "current": current,
                    "total": self.total,
                    "percentage": percentage,
                    "elapsed_seconds": elapsed_time,
                },
            )
        elif not self.total and message:
            self.logger.info(f"{self.operation}: {message}")
