import os
import shlex
import crypt
import socket
import yaml
from functools import partial
import salt.config
import salt.wheel
import salt.client
import pytest
from utils import (
    block_until_log_shows_message, start_process,
    check_output, delete_minion_key
)
from config import (
    SALT_MASTER_START_CMD, SALT_MINION_START_CMD
)


@pytest.fixture(scope="session")
def salt_root(tmpdir_factory):
    return tmpdir_factory.mktemp("salt")


@pytest.fixture(scope="session")
def user():
    return check_output(['whoami']).strip()


def delete_salt_api_user(username):
    cmd = "userdel {0}".format(username)
    check_output(shlex.split(cmd))


@pytest.fixture(scope="session")
def salt_api_user(request, env):
    user = env['CLIENT_USER']
    password_salt = '00'
    password = crypt.crypt(env['CLIENT_PASSWORD'], password_salt)
    cmd = "useradd {0} -p '{1}'".format(user, password)
    output = check_output(shlex.split(cmd))
    request.addfinalizer(partial(delete_salt_api_user, env['CLIENT_USER']))
    return output


@pytest.fixture(scope="session")
def wheel_client(master_config, master):
    opts = salt.config.master_config(master_config.strpath)
    client = salt.wheel.WheelClient(opts)
    return client


@pytest.fixture(scope="session")
def local_client(master_config, master):
    return salt.client.LocalClient(master_config.strpath)


@pytest.fixture(scope="session")
def caller_client(minion_config):
    opts = salt.config.minion_config(minion_config.strpath)
    caller = salt.client.Caller(mopts=opts)
    return caller


@pytest.fixture(scope="session")
def master_config(salt_root, env):
    config_file = salt_root / 'master'
    config = {
        'user': env['USER'],
        'pidfile': '{0}/run/salt-master.pid'.format(env['SALT_ROOT']),
        'root_dir': env['SALT_ROOT'],
        'pki_dir': '{0}/pki/'.format(env['SALT_ROOT']),
        'cachedir': '{0}/cache/'.format(env['SALT_ROOT']),
        'hash_type': env['HASH_TYPE'],
        'pillar_roots': {
            'base': [env['PILLAR_ROOT']]
        },
        'file_roots': {
            'base': [env['FILE_ROOTS']]
        },
        'external_auth': {
            'pam': {env['CLIENT_USER']: ['.*', '@wheel', '@runner', '@jobs']}}
    }
    config_file.write(yaml.dump(config))
    return config_file


@pytest.fixture(scope="session")
def pillar_root(salt_root):
    return salt_root.mkdir('pillar')


@pytest.fixture(scope="session")
def file_roots(salt_root):
    return salt_root.mkdir('topfiles')


@pytest.fixture(scope="session")
def minion_config(salt_root, env):
    config_file = salt_root / 'minion'
    config = {
        'user': env['USER'],
        'master': 'localhost',
        'pidfile': '{0}/run/salt-minion.pid'.format(env['SALT_ROOT']),
        'root_dir': env['SALT_ROOT'],
        'pki_dir': '{0}/pki/'.format(env['SALT_ROOT']),
        'cachedir': '{0}/cache/'.format(env['SALT_ROOT']),
        'hash_type': 'sha384',
    }
    config_file.write(yaml.dump(config))
    return config_file


@pytest.fixture(scope="session")
def proxy_server_port(request):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in xrange(8001, 8010):
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            continue
        else:
            break
    else:
        raise Exception(
            "Could not start the proxy minion api server. All ports are taken"
        )
    return str(port)


@pytest.fixture(scope="session")
def env(salt_root, file_roots, pillar_root, user, proxy_server_port):
    env = dict(os.environ)
    env["USER"] = user
    env["SALT_ROOT"] = salt_root.strpath
    env["PROXY_ID"] = "proxy-minion"
    env["PROXY_SERVER_PORT"] = proxy_server_port
    env["CLIENT_USER"] = "salt_api_user"
    env["CLIENT_PASSWORD"] = "linux"
    env["FILE_ROOTS"] = file_roots.strpath
    env["PILLAR_ROOT"] = pillar_root.strpath
    env['HASH_TYPE'] = 'sha384'
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


@pytest.fixture(scope="module")
def minion_highstate(env, minion_ready, local_client):
    res = local_client.cmd(env['HOSTNAME'], 'state.highstate')
    assert 'pkgrepo_|-systemsmanagement_saltstack_|-systemsmanagement_saltstack_|-managed' in res[env['HOSTNAME']]
