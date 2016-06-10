import pytest
import yaml
import salt.config
import salt.wheel
from docker import Client


@pytest.fixture(scope="session")
def salt_api_user():
    pass


@pytest.fixture(scope="session")
def master_config():
    pass


@pytest.fixture(scope="session")
def minion_config():
    pass


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
def salt_minion_config(master, minion_root, env, docker_client):
    config_file = minion_root / 'minion'
    data = docker_client.inspect_container('master')
    master_ip = data['NetworkSettings']['IPAddress']
    config = {
        'master': master_ip,
        'id': 'minime',
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
    import crypt
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


def test_master_accept_minion(env, start_salt_master, start_salt_minion, wheel_client):
    from functools import partial
    list_keys = partial(
        wheel_client.cmd_sync,
        dict(
            fun='key.list_all',
            eauth="pam",
            username=env['CLIENT_USER'],
            password=env['CLIENT_PASSWORD']
        )
    )
    import time
    time.sleep(15)
    assert ['minime'] == list_keys()['data']['return']['minions_pre']
