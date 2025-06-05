import functools
import logging
import time

from config import DEBUG_MODE

logger = logging.getLogger(__name__)


def log_timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        if DEBUG_MODE:
            logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper
