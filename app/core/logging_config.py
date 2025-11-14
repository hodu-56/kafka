"""Logging configuration using structlog."""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import Processor

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure structured logging."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Configure structlog
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.debug:
        # Pretty printing for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_correlation_id_processor() -> Processor:
    """Processor to add correlation ID to log entries."""
    def processor(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        # Add correlation ID if available in context
        # This could be enhanced with proper context management
        return event_dict
    return processor