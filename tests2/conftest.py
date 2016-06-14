import time
from docker import Client
import pytest
from factories import ContainerFactory, MasterFactory, MinionFactory


@pytest.fixture(scope="session")
def docker_client():
    client = Client(base_url='unix://var/run/docker.sock')
    return client


@pytest.fixture(scope="session")
def salt_root(tmpdir_factory):
    return tmpdir_factory.mktemp("salt")


@pytest.fixture(scope="session")
def pillar_root(salt_root):
    return salt_root.mkdir('pillar')


@pytest.fixture(scope="session")
def file_root(salt_root):
    return salt_root.mkdir('topfiles')


@pytest.fixture(scope="module")
def salt_master_config(file_root, pillar_root):
    return {
        'hash_type': 'sha384',
        'pillar_roots': {
            'base': [pillar_root.strpath]
        },
        'file_roots': {
            'base': [file_root.strpath]
        }
    }


@pytest.fixture(scope="module")
def salt_minion_config(master_container, salt_root, docker_client):
    data = docker_client.inspect_container(master_container['config']['name'])
    master_ip = data['NetworkSettings']['IPAddress']
    return {
        'master': master_ip,
        'id': 'minime',
        'hash_type': 'sha384',
    }


@pytest.fixture(scope="module")
def master_container(request, salt_root, salt_master_config, docker_client):
    obj = ContainerFactory(
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__master=True,
        config__salt_config__post__base_config=salt_master_config
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


@pytest.fixture(scope="module")
def minion_container(request, salt_root, salt_minion_config, docker_client):
    obj = ContainerFactory(
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__minion=True,
        config__salt_config__post__base_config=salt_minion_config
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def master(request, master_container):
    return MasterFactory(container=master_container)


@pytest.fixture(scope="module")
def minion(request, minion_container):
    return MinionFactory(container=minion_container)


@pytest.fixture(scope='module')
def minion_key_cached(master, salt_minion_config):
    time.sleep(10)
    minion_id = salt_minion_config['id']
    assert minion_id in master.salt_key(minion_id)['minions_pre']


@pytest.fixture(scope='module')
def minion_key_accepted(master, minion, salt_minion_config, minion_key_cached):
    minion_id = salt_minion_config['id']
    master.salt_key_accept(minion_id)
    assert minion_id in master.salt_key()['minions']
    time.sleep(5)
