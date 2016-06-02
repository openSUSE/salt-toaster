import re
import time
import shlex
import subprocess
from config import TIME_LIMIT


class TimeLimitReached(Exception):

    """Used in tests to limit blocking time."""


def accept_key(wheel_client, key, user, password):
    output = wheel_client.cmd_sync(
        dict(
            fun='key.accept',
            match=key,
            eauth="pam",
            username=user,
            password=password
        )
    )
    assert output['data']['success']
    return output


def time_limit_reached(start_time):
    if TIME_LIMIT < (time.time() - start_time):
        raise TimeLimitReached


def block_until_log_shows_message(log_file, message):
    start_time = time.time()
    has_message = False
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


def get_suse_release():
    info = dict()
    with open('/etc/SuSE-release', 'rb') as f:
        for line in f.readlines():
            match = re.match('([a-zA-Z]+)\s*=\s*(\d+)', line)
            if match:
                info.update([[match.group(1), int(match.group(2))]])
    return info
