import os
import psutil
import shlex
from functools import partial
import salt.config
import salt.wheel
import pytest
from jinja2 import Environment, PackageLoader
from utils import (
    block_until_log_shows_message, start_process,
    check_output, delete_minion_key
)
from config import (
    SALT_MASTER_START_CMD, SALT_MINION_START_CMD, SALT_KEY_CMD
)


@pytest.fixture(scope="session")
def salt_root(tmpdir_factory):
    return tmpdir_factory.mktemp("salt")


@pytest.fixture(scope="session")
def user():
    return check_output(['whoami']).strip()


@pytest.fixture(scope="session")
def wheel_client(master_config, master):
    opts = salt.config.master_config(master_config.strpath)
    client = salt.wheel.WheelClient(opts)
    return client


@pytest.fixture(scope="session")
def master_config(salt_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('master')
    config = template.render(**env)
    config_file = salt_root / 'master'
    with config_file.open('wb') as f:
        f.write(config)
    return config_file


@pytest.fixture(scope="session")
def pillar_root(salt_root):
    return salt_root.mkdir('pillar')


@pytest.fixture(scope="session")
def minion_config(salt_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('minion')
    config = template.render(**env)
    with (salt_root / 'minion').open('wb') as f:
        f.write(config)


@pytest.fixture(scope="session")
def proxy_server_port(request):
    for port in xrange(8001, 8010):
        if port in [it.laddr[1] for it in psutil.net_connections()]:
            continue
        else:
            break
    else:
        raise Exception, "Could not start the proxy server. All ports are taken"
    return str(port)


@pytest.fixture(scope="session")
def env(salt_root, user, proxy_server_port):
    env = dict(os.environ)
    env["USER"] = user
    env["SALT_ROOT"] = salt_root.strpath
    env["PROXY_ID"] = "proxy-minion"
    env["PROXY_SERVER_PORT"] = proxy_server_port
    env["CLIENT_USER"] = "test"
    env["CLIENT_PASSWORD"] = "test"
    return env


@pytest.fixture(scope="session")
def master(request, master_config, env):
    return start_process(request, SALT_MASTER_START_CMD, env)


@pytest.fixture(scope="module")
def minion(request, minion_config, wheel_client, env, context):
    context['MINION_KEY'] = env['HOSTNAME']
    request.addfinalizer(
        partial(delete_minion_key, wheel_client, context['MINION_KEY'], env)
    )
    return start_process(request, SALT_MINION_START_CMD, env)


@pytest.fixture(scope="session")
def wait_minion_key_cached(salt_root):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/minion'),
        message='Salt Master has cached the public key'
    )


@pytest.fixture(scope="module")
def context():
    return dict()


@pytest.fixture(scope="module")
def accept_key(request, context, env, salt_root, wheel_client):
    output = wheel_client.cmd_sync(
        dict(
            fun='key.accept',
            match=context['MINION_KEY'],
            eauth="pam",
            username=env['CLIENT_USER'],
            password=env['CLIENT_PASSWORD']
        )
    )
    assert output['data']['success']
    return output


@pytest.fixture(scope="module")
def minion_ready(env, salt_root, accept_key):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/minion'),
        message='Minion is ready to receive requests!'
    )
