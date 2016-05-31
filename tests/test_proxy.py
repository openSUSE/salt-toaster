import pytest
import time
import shlex
import yaml
import json
import requests
from functools import partial
from utils import (
    block_until_log_shows_message, start_process, check_output,
    delete_minion_key
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
    config_file = salt_root / 'proxy'
    config = {
        'user': env['USER'],
        'master': 'localhost',
        'pidfile': '{0}/run/salt-proxyminion.pid'.format(env['SALT_ROOT']),
        'root_dir': env['SALT_ROOT'],
        'pki_dir': '{0}/pki/'.format(env['SALT_ROOT']),
        'cachedir': '{0}/cache/'.format(env['SALT_ROOT']),
        'hash_type': 'sha384',
    }
    config_file.write(yaml.dump(config))
    return config_file


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
def proxyminion(request, proxyminion_config, wait_proxy_server_ready, wheel_client, env, context):
    context['MINION_KEY'] = env['PROXY_ID']
    request.addfinalizer(
        partial(delete_minion_key, wheel_client, context['MINION_KEY'], env)
    )
    return start_process(request, SALT_PROXYMINION_START_CMD, env)


@pytest.fixture(scope="module")
def wait_proxyminion_key_cached(salt_root):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/proxy'),
        message='Salt Master has cached the public key'
    )


@pytest.fixture(scope="module")
def proxyminion_ready(env, salt_root, accept_key):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/proxy'),
        message='Proxy Minion is ready to receive requests!'
    )


def test_proxyminion_key_cached(env):
    assert_proxyminion_key_state(env, "unaccepted")


def test_proxyminion_key_accepted(env, accept_key):
    assert_proxyminion_key_state(env, "accepted")


def test_ping_proxyminion(env, proxyminion_ready):
    cmd = shlex.split(SALT_PROXY_CALL.format(**env))
    cmd.append("test.ping")
    output = json.loads(check_output(cmd, env))
    assert output[env['PROXY_ID']] is True
