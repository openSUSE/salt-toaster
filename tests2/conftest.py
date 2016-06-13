import yaml
from docker import Client
import pytest
from factories import MasterFactory, MinionFactory


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
def salt_master_config(master_root, file_root, pillar_root):
    config_file = master_root / 'master'
    config = {
        'hash_type': 'sha384',
        'pillar_roots': {
            'base': [pillar_root.strpath]
        },
        'file_roots': {
            'base': [file_root.strpath]
        }
    }
    config_file.write(yaml.safe_dump(config, default_flow_style=False))
    return dict(file=config_file, config=config)


@pytest.fixture(scope="module")
def salt_minion_config(master_container, minion_root):
    config_file = minion_root / 'minion'
    docker_client = master_container['container']['docker_client']
    master_name = master_container['container']['config']['name']
    data = docker_client.inspect_container(master_name)
    master_ip = data['NetworkSettings']['IPAddress']
    config = {
        'master': master_ip,
        'id': 'minime',
        'hash_type': 'sha384',
    }
    yaml_content = yaml.safe_dump(config, default_flow_style=False)
    config_file.write(yaml_content)
    return dict(file=config_file, config=config)


@pytest.fixture(scope="module")
def start_salt_master(master_container):
    docker_client = master_container['container']['docker_client']
    res = docker_client.exec_create(
        master_container['container']['config']['name'],
        cmd='salt-master -d -l debug'
    )
    return docker_client.exec_start(res['Id'])


@pytest.fixture(scope="module")
def start_salt_minion(minion_container):
    docker_client = minion_container['container']['docker_client']
    start_minion = docker_client.exec_create(
        minion_container['container']['config']['name'],
        cmd='salt-minion -d -l debug'
    )
    return docker_client.exec_start(start_minion['Id'])


@pytest.fixture(scope="session")
def pillar_root(salt_root):
    return salt_root.mkdir('pillar')


@pytest.fixture(scope="session")
def file_root(salt_root):
    return salt_root.mkdir('topfiles')


@pytest.fixture(scope="module")
def master_container(request, master_root, salt_master_config, docker_client):
    obj = MasterFactory(
        container__config__salt_config__root=master_root,
        container__docker_client=docker_client
    )
    request.addfinalizer(
        lambda: obj['container']['docker_client'].remove_container(
            obj['container']['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def master(request, master_container, start_salt_master):
    return master_container


@pytest.fixture(scope="module")
def minion_container(request, minion_root, salt_minion_config, docker_client):
    obj = MinionFactory(
        container__config__salt_config__root=minion_root,
        container__docker_client=docker_client
    )
    request.addfinalizer(
        lambda: obj['container']['docker_client'].remove_container(
            obj['container']['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def minion(request, minion_container, start_salt_minion):
    return minion_container
