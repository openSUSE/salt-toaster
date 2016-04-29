import time
from config import TIME_LIMIT
from exceptions import TimeLimitReached


def time_limit_reached(start_time):
    if TIME_LIMIT < (time.time() - start_time):
        raise TimeLimitReached


def block_until_log_shows_message(log_file, message):
    start_time = time.time()
    has_message = False
    try:
        while not log_file.exists() and not time_limit_reached(start_time):
            time.sleep(0.1)
        with log_file.open('rb') as f:
            start_time = time.time()
            while not has_message and not time_limit_reached(start_time):
                line = f.readline().strip()
                if not line:
                    time.sleep(0.1)
                    continue
                has_message = message in line
    except TimeLimitReached:
        # time limit reached so we just return
        pass
    return has_message
