import functools
import inspect
import logging
import os
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


# In jupyter lab, it's convenient for other functions to move to src dir. However that messes up input/output dir. So I'm adding optionality for both.
def jupyter_src_path_fix(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the function signature and bind the arguments
        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()

        input_dir = bound_args.arguments.get("input_dir") or os.environ.get("WORKING_FOLDER")
        output_dir = bound_args.arguments.get("output_dir") or os.environ.get("DOWNLOAD_FOLDER")

        # If in 'src' dir, adjust paths if needed
        if os.path.basename(os.getcwd()) == "src":
            if input_dir and not input_dir.startswith("../"):
                input_dir = "../" + input_dir
            if output_dir and not output_dir.startswith("../"):
                output_dir = "../" + output_dir

        # Update the arguments safely
        bound_args.arguments["input_dir"] = input_dir
        bound_args.arguments["output_dir"] = output_dir

        return func(*bound_args.args, **bound_args.kwargs)

    return wrapper
