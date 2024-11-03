import functools
import logging
import time


logger = logging.getLogger(__name__)


def print_time(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = function(*args, **kwargs)
        end_time = time.monotonic()
        logger.debug(
            f"{function.__name__} with {args=!r} {kwargs=!r} took {end_time - start_time} s"
        )
        return result

    return wrapper
