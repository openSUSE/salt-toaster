import datetime
import os
import re
import time
from jinja2 import Environment, FileSystemLoader
from py.path import local as path
from docker import Client

from config import TIME_LIMIT


class TimeLimitReached(Exception):

    """Used in tests to limit blocking time."""


def time_limit_reached(start_time):
    if TIME_LIMIT < (time.time() - start_time):
        raise TimeLimitReached


def _dos(func):
    return func() is True


def retry(func, definition_of_success=_dos):
    success = False
    start_time = time.time()
    while not success and not time_limit_reached(start_time):
        if getattr(func, 'func', False):
            # not a normal function but one wrapped with functools.partial
            print('retry: ' + func.func.func_name)
        else:
            print('retry: ' + func.func_name)
        success = definition_of_success(func)
        if success is not True:
            time.sleep(1)
            continue
    return success
