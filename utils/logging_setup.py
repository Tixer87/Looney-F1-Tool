"""Centralized logging configuration for Looney F1 Tool.

Provides:
- Rotating file handler + console handler
- Configurable log levels (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- Context logger adapter for structured logging with key=value pairs
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


def get_logger(
    name: str,
    level: str = "INFO",
    logfile: str | None = None
) -> logging.Logger:
    """Get or create a logger with console and rotating file handlers.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        logfile: Path to log file. If None, uses 'logs/app.log'
    
    Returns:
        Configured logger instance
    
    Idempotent: Multiple calls with same name won't add duplicate handlers.
    """
    logger = logging.getLogger(name)
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Check if handlers already exist (idempotent)
    has_stream = any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) 
                     for h in logger.handlers)
    has_file = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
    
    # Standard format: timestamp level name: message
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add StreamHandler (stdout) if not present
    if not has_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(numeric_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    
    # Add RotatingFileHandler if not present
    if not has_file:
        # Default logfile location
        if logfile is None:
            logfile = "logs/app.log"
        
        # Ensure directory exists
        log_path = Path(logfile)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating handler: 1MB max, 5 backups
        file_handler = RotatingFileHandler(
            logfile,
            maxBytes=1_000_000,  # 1 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger (avoid duplicate logs)
    logger.propagate = False
    
    return logger


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that appends key=value pairs from extra dict to messages.
    
    Example:
        log = ContextLoggerAdapter(logger, {"provider": "jolpica", "session": "Q"})
        log.info("fetch start", attempt=1)
        # Output: "2025-11-01 12:00:00 INFO api.provider: fetch start provider=jolpica session=Q attempt=1"
    """
    
    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Process log message by appending context key=value pairs."""
        # Merge base extra with call-time kwargs
        extra = self.extra.copy() if self.extra else {}
        
        # Extract any extra kwargs passed to log call (non-logging args)
        # We need to pop them from kwargs to avoid TypeError in Logger._log
        context_keys = [k for k in kwargs.keys() if k not in ('exc_info', 'stack_info', 'stacklevel', 'extra')]
        for key in context_keys:
            extra[key] = kwargs.pop(key)
        
        # Build key=value suffix from extra dict
        context_parts = [f"{k}={v}" for k, v in extra.items()]
        
        # Append to message
        if context_parts:
            msg = f"{msg} {' '.join(context_parts)}"
        
        return msg, kwargs


def get_context_logger(
    name: str,
    base_extra: dict | None = None,
    level: str = "INFO",
    logfile: str | None = None,
    **kwargs
) -> ContextLoggerAdapter:
    """Get a context logger adapter with merged extra dict.
    
    Args:
        name: Logger name (typically __name__)
        base_extra: Base context dict (e.g., {"provider": "jolpica"})
        level: Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        logfile: Path to log file. If None, uses 'logs/app.log'
        **kwargs: Additional context key=value pairs
    
    Returns:
        ContextLoggerAdapter with merged context
    
    Example:
        log = get_context_logger(__name__, {"provider": "fastf1"}, session="R")
        log.info("cache hit", duration_ms=120)
        # Output includes: provider=fastf1 session=R duration_ms=120
    """
    logger = get_logger(name, level=level, logfile=logfile)
    
    # Merge base_extra with kwargs
    extra = base_extra.copy() if base_extra else {}
    extra.update(kwargs)
    
    return ContextLoggerAdapter(logger, extra)
