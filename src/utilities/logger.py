import sys
from loguru import logger

logger.remove()
logger.add("logs/aster_oi_bot.log", rotation="10 MB", retention="7 days", enqueue=True)
logger.add(sys.stderr, enqueue=True)

__all__ = ["logger"]