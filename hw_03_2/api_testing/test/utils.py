import functools
import logging


logging.basicConfig(filename=None, level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for i, c in enumerate(cases):
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except Exception as e:
                    logging.error(f"Error while testing {f.__name__} with case number {i + 1}: {c}.")
                    raise e
        return wrapper
    return decorator

