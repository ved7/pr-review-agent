from __future__ import annotations

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="{time} | {level} | {message}",
        colorize=True,
    )


__all__ = ["setup_logging", "logger"]
