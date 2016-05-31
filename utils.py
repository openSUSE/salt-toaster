import time
import shlex
import subprocess
from config import TIME_LIMIT


class TimeLimitReached(Exception):

    """Used in tests to limit blocking time."""


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


def start_process(request, cmd, env):
    proc = subprocess.Popen(
        shlex.split(cmd.format(**env)), stdout=subprocess.PIPE, env=env)
    assert proc.returncode is None
    request.addfinalizer(proc.terminate)
    return proc


def check_output(cmd, env=None):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
    output, unused_err = process.communicate()
    return output


def delete_minion_key(wheel_client, key, env):
    output = wheel_client.cmd_sync(
        dict(
            fun='key.delete',
            match=key,
            eauth="pam",
            username=env['CLIENT_USER'],
            password=env['CLIENT_PASSWORD']
        )
    )
    assert output['data']['success']