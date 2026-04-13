"""
NexaCart AI Support Bot - Logging Configuration

Provides a configured logger with both file and console output, plus a
structured interaction logger for analytics.
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional

from app.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_configured: bool = False


def _configure_root_logger() -> None:
    """Configure the root logger once with file and stream handlers."""
    global _configured
    if _configured:
        return

    # Ensure log directory exists
    log_dir = os.path.dirname(settings.LOG_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = logging.FileHandler(settings.LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Ensures the root logger has been configured first.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    _configure_root_logger()
    return logging.getLogger(name)


def log_interaction(
    session_id: str,
    query: str,
    response: str,
    confidence: float,
    is_fallback: bool,
    sources: Optional[list] = None,
) -> None:
    """
    Log a structured JSON record for each chat interaction.

    Args:
        session_id: The user's session identifier.
        query: The raw customer query.
        response: The answer returned by the bot.
        confidence: Computed confidence score (0.0–1.0).
        is_fallback: Whether the response is the fallback escalation message.
        sources: Optional list of source dicts included in the response.
    """
    logger = get_logger("interaction")
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "query": query,
        "response_preview": response[:120],
        "confidence": round(confidence, 4),
        "is_fallback": is_fallback,
        "source_count": len(sources) if sources else 0,
    }
    logger.info("INTERACTION | %s", json.dumps(record, ensure_ascii=False))
