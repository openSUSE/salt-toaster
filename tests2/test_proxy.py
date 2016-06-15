import time
import pytest
from faker import Faker
from factories import ContainerFactory, MinionFactory


PROXY_MINION_ID = 'proxy_minion'
PROXY_SERVER_PORT = 8000


@pytest.fixture(scope="module")
def salt_master_config(file_root, pillar_root):
    return {
        'base_config': {
            'pillar_roots': {'base': [pillar_root]},
            'file_roots': {'base': [file_root]}
        }
    }


@pytest.fixture(scope="module")
def master_container(request, salt_root, docker_client, proxy_server, salt_master_config):
    obj = ContainerFactory(
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__master=True,
        config__salt_config__post__config=salt_master_config,
        config__salt_config__post__pillar={
            'top': {'base': {PROXY_MINION_ID: [PROXY_MINION_ID]}},
            PROXY_MINION_ID: {
                'proxy': {
                    'proxytype': 'rest_sample',
                    'url': 'http://{0}:{1}'.format(
                        proxy_server['ip'], PROXY_SERVER_PORT
                    )
                }
            }
        }
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


@pytest.fixture(scope="module")
def minion_container(request, salt_root, docker_client, master_container):
    obj = ContainerFactory(
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__proxy=True,
        config__salt_config__id=PROXY_MINION_ID,
        config__salt_config__post__config={
            'base_config': {'master': master_container['ip']}
        }
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True))
    return obj


@pytest.fixture(scope='module')
def minion_key_accepted(master):
    time.sleep(10)
    assert PROXY_MINION_ID in master.salt_key(PROXY_MINION_ID)['minions_pre']
    master.salt_key_accept(PROXY_MINION_ID)
    assert PROXY_MINION_ID in master.salt_key()['minions']
    time.sleep(5)


@pytest.fixture(scope="module")
def minion(request, minion_container):
    return MinionFactory(
        container=minion_container,
        cmd='salt-proxy -d -l debug --proxyid proxy_minion'
    )


@pytest.fixture(scope="module")
def proxy_server(request, salt_root, docker_client):
    fake = Faker()
    name = u'proxy_server_{0}_{1}'.format(fake.word(), fake.word())
    command = 'python -m tests.proxy_server {0}'.format(PROXY_SERVER_PORT)
    obj = ContainerFactory(
        docker_client=docker_client,
        config__command=command,
        config__name=name,
        config__salt_config__tmpdir=salt_root,
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True))
    return obj


def test_ping_proxyminion(master, minion, minion_key_accepted):
    assert master.salt(PROXY_MINION_ID, "test.ping")[PROXY_MINION_ID] is True
