import functools
import logging
import time
from typing import Callable

from config import DEBUG_MODE

logger = logging.getLogger(__name__)


def log_timing(func: Callable) -> Callable:
    """Decorator to log the execution time of a function.

    :param func: The function to decorate.

    :returns: The decorated function.

    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        if DEBUG_MODE:
            logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


def sanitize_string(input_string: str) -> str:
    """Sanitize the input string by normalizing unicode characters to their decomposed form, then encoding to utf-8.

    :returns: Sanitized string

    :params input_string: String to sanitize

    """
    text = str(input_string)
    try:
        encoded_string = text.encode("utf-8")
        sanitized_string = encoded_string.decode("utf-8")
    except UnicodeEncodeError:
        sanitized_string = text.encode("utf-8", errors="replace").decode("utf-8")
    return sanitized_string
