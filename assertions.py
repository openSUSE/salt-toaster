import json
import shlex
import subprocess
from config import SALT_KEY_CMD


STATES_MAPPING = dict(unaccepted='minions_pre', accepted='minions')


def get_keys_status(env):
    cmd = shlex.split(SALT_KEY_CMD.format(**env))
    cmd.append("-L")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
    output, unused_err = process.communicate()
    return json.loads(output)


def assert_minion_key_state(env, expected_state):
    assert expected_state in STATES_MAPPING
    status = get_keys_status(env)
    assert env['HOSTNAME'] in status[STATES_MAPPING[expected_state]], status


def assert_proxyminion_key_state(env, expected_state):
    assert expected_state in STATES_MAPPING
    status = get_keys_status(env)
    assert env['PROXY_ID'] in status[STATES_MAPPING[expected_state]], status
