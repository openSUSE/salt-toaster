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
    salt_root.mkdir('pillar')
    return '/etc/salt/pillar'


@pytest.fixture(scope="session")
def file_root(salt_root):
    salt_root.mkdir('topfiles')
    return '/etc/salt/topfiles'


@pytest.fixture(scope="module")
def salt_master_config(file_root, pillar_root):
    return {
        'base_config': {
            'hash_type': 'sha384',
            'pillar_roots': {
                'base': [pillar_root]
            },
            'file_roots': {
                'base': [file_root]
            }
        }
    }


@pytest.fixture(scope="module")
def salt_minion_config(master_container, salt_root, docker_client):
    return {
        'master': master_container['ip'],
        'hash_type': 'sha384',
    }


@pytest.fixture(scope="module")
def master_container(request, salt_root, salt_master_config, docker_client):
    obj = ContainerFactory(
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__master=True,
        config__salt_config__post__config=salt_master_config
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
        config__salt_config__post__config={
            'base_config': salt_minion_config
        }
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
def minion_key_cached(master, minion):
    time.sleep(10)
    minion_id = minion['container']['config']['name']
    assert minion_id in master.salt_key(minion_id)['minions_pre']


@pytest.fixture(scope='module')
def minion_key_accepted(master, minion, minion_key_cached):
    minion_id = minion['container']['config']['name']
    master.salt_key_accept(minion_id)
    assert minion_id in master.salt_key()['minions']
    time.sleep(5)
