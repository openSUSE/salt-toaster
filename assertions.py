import shlex
import subprocess
from config import SALT_KEY_CMD


def assert_minion_key_state(env, expected_state):
    STATES_MAPPING = dict(
        unaccepted="Unaccepted Keys:\n{HOSTNAME}".format(**env),
        accepted="Accepted Keys:\n{HOSTNAME}".format(**env)
    )
    assert expected_state in STATES_MAPPING
    cmd = shlex.split(SALT_KEY_CMD.format(**env))
    cmd.append("-L")
    assert STATES_MAPPING[expected_state] in subprocess.check_output(cmd, env=env)


def assert_proxyminion_key_state(env, expected_state):
    STATES_MAPPING = dict(
        unaccepted="Unaccepted Keys:\n{PROXY_ID}".format(**env),
        accepted="Accepted Keys:\n{PROXY_ID}".format(**env)
    )
    assert expected_state in STATES_MAPPING
    cmd = shlex.split(SALT_KEY_CMD.format(**env))
    cmd.append("-L")
    output = subprocess.check_output(cmd, env=env)
    assert STATES_MAPPING[expected_state] in output
