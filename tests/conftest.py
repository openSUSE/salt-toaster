from docker import Client
import pytest
from faker import Faker
from utils import retry
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
def minion_config():
    fake = Faker()
    return {'id': u'{0}_{1}'.format(fake.word(), fake.word())}


@pytest.fixture(scope="module")
def salt_minion_config(master_container, salt_root, docker_client):
    return {
        'master': master_container['ip'],
        'hash_type': 'sha384',
    }


@pytest.fixture(scope="module")
def master_container(request, salt_root, salt_master_config, docker_client):
    fake = Faker()
    obj = ContainerFactory(
        config__name='master_{0}_{1}'.format(fake.word(), fake.word()),
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__conf_type='master',
        config__salt_config__config=salt_master_config,
        config__salt_config__post__id='{0}_{1}'.format(fake.word(), fake.word())
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


@pytest.fixture(scope="module")
def minion_container(request, salt_root, salt_minion_config, docker_client, minion_config):
    fake = Faker()
    obj = ContainerFactory(
        config__name='minion_{0}_{1}'.format(fake.word(), fake.word()),
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__conf_type='minion',
        config__salt_config__config={
            'base_config': salt_minion_config
        },
        config__salt_config__post__id=minion_config['id']
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def master(request, master_container):
    return MasterFactory(container=master_container)


@pytest.fixture(scope="module")
def minion(request, minion_container, minion_config):
    out = MinionFactory(container=minion_container)
    out.setdefault('id', minion_config['id'])
    return out


@pytest.fixture(scope='module')
def minion_key_cached(master, minion, minion_config):
    minion_id = minion_config['id']

    def cache():
        return minion_id in master.salt_key(minion_id)['minions_pre']

    assert retry(cache) is True


@pytest.fixture(scope='module')
def minion_key_accepted(master, minion, minion_key_cached, minion_config):
    minion_id = minion_config['id']
    master.salt_key_accept(minion_id)

    def accept():
        return minion_id in master.salt_key()['minions']

    assert retry(accept) is True
