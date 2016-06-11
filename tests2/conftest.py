import os
import time
import shlex
import yaml
from docker import Client
import pytest
from utils import check_output


@pytest.fixture(scope="module")
def context():
    return dict(
        master=dict(
            container=dict(
                name='master'
            )
        ),
        minion=dict(
            container=dict(
                name='minion'
            ),
            salt=dict(
                id='minime'
            )
        )
    )


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
def master_docker_image(salt_root, docker_client):
    tag = 'registry.mgr.suse.de/toaster-sles12sp1'
    output = docker_client.build(
        os.getcwd() + '/tests2/docker/sles12sp1/',
        tag=tag,
        pull=True,
        decode=True,
        # nocache=True
    )
    for item in output:
        print item.values()[0]
    return tag


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
        }
    }
    config_file.write(yaml.safe_dump(config, default_flow_style=False))
    return dict(file=config_file, config=config)


@pytest.fixture(scope="module")
def master_docker_config(env, context, salt_master_config, master_docker_image, master_root, docker_client):
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
        name=context['master']['container']['name'],
        image=master_docker_image,
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
def master_container(request, context, docker_client, master_docker_config):
    request.addfinalizer(
        lambda: docker_client.remove_container(context['master']['container']['name'], force=True))
    master_container = docker_client.create_container(**master_docker_config)
    docker_client.start(context['master']['container']['name'])
    return master_container


@pytest.fixture(scope="module")
def minion_root(salt_root):
    return salt_root.mkdir("minion")


@pytest.fixture(scope="module")
def salt_minion_config(context, master_docker_config, minion_root, docker_client):
    config_file = minion_root / 'minion'
    data = docker_client.inspect_container(context['master']['container']['name'])
    master_ip = data['NetworkSettings']['IPAddress']
    config = {
        'master': master_ip,
        'id': context['minion']['salt']['id'],
        'hash_type': 'sha384',
    }
    yaml_content = yaml.safe_dump(config, default_flow_style=False)
    config_file.write(yaml_content)
    return dict(file=config_file, config=config)


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
def start_salt_master(docker_client, master_container):
    res = docker_client.exec_create(
        master_container['Id'], cmd='salt-master -d -l debug')
    return docker_client.exec_start(res['Id'])


@pytest.fixture(scope="module")
def start_salt_minion(docker_client, minion_container):
    start_minion = docker_client.exec_create(
        minion_container['Id'], cmd='salt-minion -d -l debug')
    return docker_client.exec_start(start_minion['Id'])


@pytest.fixture(scope="session")
def user():
    return check_output(['whoami']).strip()


def delete_salt_api_user(username):
    cmd = "userdel {0}".format(username)
    check_output(shlex.split(cmd))


@pytest.fixture(scope="session")
def pillar_root(salt_root):
    return salt_root.mkdir('pillar')


@pytest.fixture(scope="session")
def file_roots(salt_root):
    return salt_root.mkdir('topfiles')


@pytest.fixture(scope="session")
def env(salt_root, file_roots, pillar_root, user):
    env = dict(os.environ)
    env["USER"] = user
    env["SALT_ROOT"] = salt_root.strpath
    env["PROXY_ID"] = "proxy-minion"
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
