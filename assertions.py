import re
import shlex
import subprocess
from config import SALT_KEY_CMD


def has_expected_state(expected_state, mapping, env):
    assert expected_state in mapping
    cmd = shlex.split(SALT_KEY_CMD.format(**env))
    cmd.append("-L")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
    output, unused_err = process.communicate()
    return mapping[expected_state].search(output) is not None


def assert_minion_key_state(env, expected_state):
    STATES_MAPPING = dict(
        unaccepted=re.compile("Unaccepted Keys:(\n.+)*\n{HOSTNAME}".format(**env)),
        accepted=re.compile("Accepted Keys:(\n.+)*\n{HOSTNAME}".format(**env))
    )
    assert has_expected_state(expected_state, STATES_MAPPING, env)


def assert_proxyminion_key_state(env, expected_state):
    STATES_MAPPING = dict(
        unaccepted=re.compile("Unaccepted Keys:(\n.+)*\n{PROXY_ID}".format(**env)),
        accepted=re.compile("Accepted Keys:(\n.+)*\n{PROXY_ID}".format(**env))
    )
    assert has_expected_state(expected_state, STATES_MAPPING, env)
