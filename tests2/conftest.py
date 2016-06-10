import os
import shlex
import crypt
import socket
import yaml
from functools import partial
import salt.config
import salt.wheel
import salt.client
from docker import Client
import pytest
from utils import (
    block_until_log_shows_message,
    check_output, accept_key, get_suse_release
)


@pytest.fixture(scope="module")
def context():
    return dict(minion_id='minime')


@pytest.fixture(scope="session")
def docker_client():
    client = Client(base_url='unix://var/run/docker.sock')
    return client


@pytest.fixture(scope="session")
def salt_root(tmpdir_factory):
    return tmpdir_factory.mktemp("salt")


@pytest.fixture(scope="module")
def master_root(salt_root):
    return salt_root.mkdir("master")


@pytest.fixture(scope="module")
def minion_root(salt_root):
    return salt_root.mkdir("minion")


@pytest.fixture(scope="module")
def salt_master_config(master_root, env):
    config_file = master_root / 'master'
    config = {
        'hash_type': env['HASH_TYPE'],
        'pillar_roots': {
            'base': [env['PILLAR_ROOT']]
        },
        'file_roots': {
            'base': [env['FILE_ROOTS']]
        },
        'external_auth': {
            'pam': {
                env['CLIENT_USER']: ['.*', '@wheel', '@runner', '@jobs']
            }
        }
    }
    config_file.write(yaml.safe_dump(config, default_flow_style=False))
    return config_file


@pytest.fixture(scope="module")
def salt_minion_config(master, minion_root, env, context, docker_client):
    config_file = minion_root / 'minion'
    data = docker_client.inspect_container('master')
    master_ip = data['NetworkSettings']['IPAddress']
    config = {
        'master': master_ip,
        'id': context['minion_id'],
        'hash_type': 'sha384',
    }
    yaml_content = yaml.safe_dump(config, default_flow_style=False)
    config_file.write(yaml_content)
    return config_file


@pytest.fixture(scope="module")
def master_docker_config(env, salt_master_config, master_root, docker_client):
    host_config = docker_client.create_host_config(
        port_bindings={4000: 4000, 4506: 4506},
        binds={
            master_root.strpath: {
                'bind': '/etc/salt/',
                'mode': 'rw',
            },
            "/home/mdinca/repositories/salt-toaster/": {
                'bind': "/salt-toaster/",
                'mode': 'rw'
            }
        }
    )
    return dict(
        name='master',
        image='registry.mgr.suse.de/toaster-sles12sp1',
        command='/bin/bash',
        tty=True,
        stdin_open=True,
        working_dir="/salt-toaster/",
        ports=[4000, 4506],
        volumes=[
            master_root.strpath,
            "/home/mdinca/repositories/salt-toaster/"
        ],
        host_config=host_config
    )


@pytest.fixture(scope="module")
def master_container(request, docker_client, master_docker_config):
    request.addfinalizer(
        lambda: docker_client.remove_container('master', force=True))
    master_container = docker_client.create_container(**master_docker_config)
    docker_client.start('master')
    return master_container


@pytest.fixture(scope="module")
def minion_docker_config(env, minion_root, salt_minion_config, docker_client):
    host_config = docker_client.create_host_config(
        port_bindings={4000: 4001},
        binds={
            minion_root.strpath: {
                'bind': '/etc/salt/',
                'mode': 'rw',
            },
            "/home/mdinca/repositories/salt-toaster/": {
                'bind': "/salt-toaster/",
                'mode': 'rw'
            }
        }
    )
    return dict(
        name='minion',
        image='registry.mgr.suse.de/toaster-sles12sp1',
        command='/bin/bash',
        tty=True,
        stdin_open=True,
        working_dir="/salt-toaster/",
        ports=[4000],
        volumes=[minion_root.strpath, "/home/mdinca/repositories/salt-toaster/"],
        host_config=host_config
    )


@pytest.fixture(scope="module")
def minion_container(request, docker_client, minion_docker_config):
    request.addfinalizer(
        lambda: docker_client.remove_container('minion', force=True))
    minion_container = docker_client.create_container(**minion_docker_config)
    docker_client.start('minion')
    return minion_container


@pytest.fixture(scope="module")
def create_master_api_user(env, docker_client, master_container):
    user = env['CLIENT_USER']
    password_salt = '00'
    password = env['CLIENT_PASSWORD']
    encrypted_password = crypt.crypt(password, password_salt)
    res = docker_client.exec_create(
        'master', cmd="useradd {0} -p '{1}'".format(user, encrypted_password))
    return docker_client.exec_start(res['Id'])


@pytest.fixture(scope="module")
def install_salt_master(docker_client, master_container, create_master_api_user):
    res = docker_client.exec_create(
        'master', cmd='make -C /salt-toaster install_salt')
    return docker_client.exec_start(res['Id'])


@pytest.fixture(scope="module")
def start_salt_master(docker_client, install_salt_master):
    res = docker_client.exec_create('master', cmd='salt-master -d -l debug')
    return docker_client.exec_start(res['Id'])


@pytest.fixture(scope="module")
def install_salt_minion(docker_client, minion_container):
    res = docker_client.exec_create(
        'minion', cmd='make -C /salt-toaster install_salt')
    return docker_client.exec_start(res['Id'])


@pytest.fixture(scope="module")
def start_salt_minion(docker_client, install_salt_minion):
    start_minion = docker_client.exec_create(
        'minion', cmd='salt-minion -d -l debug')
    return docker_client.exec_start(start_minion['Id'])


@pytest.fixture(scope="module")
def wheel_client(salt_master_config):
    opts = salt.config.master_config(salt_master_config.strpath)
    return salt.wheel.WheelClient(opts)


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


@pytest.fixture(scope="module")
def master(start_salt_master):
    pass


@pytest.fixture(scope="module")
def minion(start_salt_minion):
    pass


@pytest.fixture(scope="module")
def wait_minion_key_cached(salt_root, minion):
    import time
    time.sleep(15)


@pytest.fixture(scope="module")
def accept_minion_key(request, context, env, salt_root, wheel_client, wait_minion_key_cached):
    return accept_key(
        wheel_client,
        context['MINION_KEY'],
        env['CLIENT_USER'],
        env['CLIENT_PASSWORD']
    )


@pytest.fixture(scope="module")
def minion_ready(env, salt_root, accept_minion_key):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/minion'),
        message='Minion is ready to receive requests!'
    )


@pytest.fixture(scope="module")
def minion_highstate(env, minion_ready, local_client):
    res = local_client.cmd(env['HOSTNAME'], 'state.highstate')
    assert 'pkgrepo_|-systemsmanagement_saltstack_|-systemsmanagement_saltstack_|-managed' in res[env['HOSTNAME']]
