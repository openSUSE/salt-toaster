import pytest
import shlex
import subprocess
from assertions import assert_proxyminion_key_state
from config import SALT_PROXY_CALL


pytestmark = pytest.mark.usefixtures(
    "master_top", "proxy_pillar", "master", "proxyminion", "wait_proxyminion_key_cached")


def test_proxyminion_key_cached(env):
    assert_proxyminion_key_state(env, "unaccepted")


def test_proxyminion_key_accepted(env, accept_keys):
    assert_proxyminion_key_state(env, "accepted")


def test_ping_proxyminion(env, proxy_server, proxyminion_ready):
    cmd = shlex.split(SALT_PROXY_CALL.format(**env))
    cmd.append("test.ping")
    output = subprocess.check_output(cmd, env=env)
    assert [env['PROXY_ID'], 'True'] == [it.strip() for it in output.split(':')]
