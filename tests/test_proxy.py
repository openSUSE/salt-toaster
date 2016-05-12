import pytest
import time
import shlex
import requests
from utils import (
    block_until_log_shows_message, start_process, check_output
)
from assertions import assert_proxyminion_key_state
from jinja2 import Environment, PackageLoader
from config import SALT_PROXY_CALL

from config import (
    SALT_PROXYMINION_START_CMD, START_PROXY_SERVER
)


pytestmark = pytest.mark.usefixtures(
    "master_top", "proxy_pillar", "master", "proxyminion", "wait_proxyminion_key_cached")


@pytest.fixture(scope="module")
def master_top(pillar_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('top.sls')
    content = template.render(**env)
    with (pillar_root / 'top.sls').open('wb') as f:
        f.write(content)


@pytest.fixture(scope="module")
def proxy_pillar(pillar_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('pillar.sls')
    content = template.render(**env)
    with (pillar_root / '{PROXY_ID}.sls'.format(**env)).open('wb') as f:
        f.write(content)


@pytest.fixture(scope="module")
def proxyminion_config(salt_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('proxy')
    config = template.render(**env)
    with (salt_root / 'proxy').open('wb') as f:
        f.write(config)


@pytest.fixture(scope="module")
def proxy_server(request, env):
    return start_process(request, START_PROXY_SERVER, env)


@pytest.fixture(scope="module")
def wait_proxy_server_ready(env, proxy_server):
    status_code = None
    fails = 0
    while not status_code and fails < 10:
        try:
            response = requests.get(
                'http://localhost:{PROXY_SERVER_PORT}'.format(**env)
            )
            status_code = response.status_code
        except requests.ConnectionError:
            fails += 1
            time.sleep(0.1)


@pytest.fixture(scope="module")
def proxyminion(request, proxyminion_config, wait_proxy_server_ready, env):
    return start_process(request, SALT_PROXYMINION_START_CMD, env)


@pytest.fixture(scope="module")
def wait_proxyminion_key_cached(salt_root):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/proxy'),
        message='Salt Master has cached the public key'
    )


@pytest.fixture(scope="module")
def proxyminion_ready(env, salt_root, accept_keys):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/proxy'),
        message='Proxy Minion is ready to receive requests!'
    )


def test_proxyminion_key_cached(env):
    assert_proxyminion_key_state(env, "unaccepted")


def test_proxyminion_key_accepted(env, accept_keys):
    assert_proxyminion_key_state(env, "accepted")


def test_ping_proxyminion(env, proxyminion_ready):
    cmd = shlex.split(SALT_PROXY_CALL.format(**env))
    cmd.append("test.ping")
    output = check_output(cmd, env)
    assert [env['PROXY_ID'], 'True'] == [it.strip() for it in output.split(':')]
