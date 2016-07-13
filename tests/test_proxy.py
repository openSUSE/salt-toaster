import os
import pytest
from utils import retry
from faker import Faker
from saltcontainers.factories import ContainerFactory


PROXY_PORT = 8000


@pytest.fixture(scope="module")
def minion_id():
    fake = Faker()
    return u'{0}_{1}'.format(fake.word(), fake.word())


@pytest.fixture(scope="module")
def proxy_server(request, salt_root, docker_client):
    fake = Faker()
    name = u'proxy_server_{0}_{1}'.format(fake.word(), fake.word())
    command = 'python -m tests.scripts.proxy_server {0}'.format(PROXY_PORT)
    obj = ContainerFactory(
        config__docker_client=docker_client,
        config__image=request.config.getini('IMAGE'),
        config__command=command,
        config__name=name,
        config__salt_config=None,
        config__host_config=docker_client.create_host_config(
            binds={
                os.getcwd(): {
                    'bind': "/salt-toaster/",
                    'mode': 'rw'
                }
            }
        ),
        config__volumes=[os.getcwd()]
    )
    request.addfinalizer(
        lambda: docker_client.remove_container(
            obj['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def master_container_extras(minion_id, proxy_server):
    proxy_url = 'http://{0}:{1}'.format(proxy_server['ip'], PROXY_PORT)
    return dict(
        config__salt_config__id=minion_id,
        config__salt_config__pillar={
            'top': {'base': {minion_id: [minion_id]}},
            minion_id: {
                'proxy': {'proxytype': 'rest_sample', 'url': proxy_url}
            }
        }
    )


@pytest.fixture(scope="module")
def minion_container_extras(minion_id):
    return dict(config__salt_config__id=minion_id)


def test_ping_proxyminion(master, minion, minion_key_accepted):

    def ping():
        return master.salt(minion['id'], "test.ping")[minion['id']] is True

    assert retry(ping) is True
