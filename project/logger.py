import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    level='DEBUG',
    format="<level>{level: <8}</level> | "
           "<level>{message}</level>"
)
