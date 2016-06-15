import time
import pytest
from faker import Faker
from factories import ContainerFactory, MinionFactory


@pytest.fixture(scope="module")
def minion_config():
    fake = Faker()
    return {'id': u'{0}_{1}'.format(fake.word(), fake.word())}


@pytest.fixture(scope="module")
def proxy_config():
    return {'port': 8000}


@pytest.fixture(scope="module")
def pillar_config(minion_config, proxy_config, proxy_server):
    minion_id = minion_config['id']
    return {
        'top': {'base': {minion_id: [minion_id]}},
        minion_id: {
            'proxy': {
                'proxytype': 'rest_sample',
                'url': 'http://{0}:{1}'.format(
                    proxy_server['ip'], proxy_config['port']
                )
            }
        }
    }


@pytest.fixture(scope="module")
def salt_master_config(salt_root, file_root, pillar_root, pillar_config):
    fake = Faker()
    return dict(
        config__name='master_' + u'{0}_{1}'.format(fake.word(), fake.word()),
        config__salt_config__tmpdir=salt_root,
        config__salt_config__master=True,
        config__salt_config__post__config={
            'base_config': {
                'pillar_roots': {'base': [pillar_root]},
                'file_roots': {'base': [file_root]}
            }
        },
        config__salt_config__post__pillar=pillar_config
    )


@pytest.fixture(scope="module")
def salt_minion_config(salt_root, master_container, minion_config):
    return dict(
        id=minion_config['id'],
        config__name='minion_' + minion_config['id'],
        config__salt_config__tmpdir=salt_root,
        config__salt_config__proxy=True,
        config__salt_config__post__config={
            'base_config': {
                'master': master_container['ip'],
            }
        }
    )


@pytest.fixture(scope="module")
def master_container(request, docker_client, salt_master_config):
    obj = ContainerFactory(docker_client=docker_client, **salt_master_config)
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


@pytest.fixture(scope="module")
def minion_container(request, salt_minion_config, docker_client):
    obj = ContainerFactory(docker_client=docker_client, **salt_minion_config)
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def minion(request, minion_container, minion_config):
    return MinionFactory(
        container=minion_container,
        cmd='salt-proxy -d -l debug --proxyid {0}'.format(minion_config['id']),
        id=minion_config['id']
    )


@pytest.fixture(scope="module")
def proxy_server(request, salt_root, docker_client, proxy_config):
    fake = Faker()
    name = u'proxy_server_{0}_{1}'.format(fake.word(), fake.word())
    command = 'python -m tests.proxy_server {0}'.format(proxy_config['port'])
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


@pytest.fixture(scope='module')
def minion_key_accepted(master, minion):
    time.sleep(10)
    assert minion['id'] in master.salt_key(minion['id'])['minions_pre']
    master.salt_key_accept(minion['id'])
    assert minion['id'] in master.salt_key()['minions']
    time.sleep(5)


def test_ping_proxyminion(master, minion, minion_key_accepted):
    assert master.salt(minion['id'], "test.ping")[minion['id']] is True
