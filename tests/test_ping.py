import time
import pytest
import logging
from faker import Faker
from saltcontainers.factories import MasterFactory, MinionFactory, ContainerFactory


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


pytestmark = pytest.mark.usefixtures("master", "minion")


def wait_cached(master, minion):
    command = 'salt-run --out json -l quiet state.event tagmatch="salt/auth"'
    for item in master['container'].run(command, stream=True):
        if minion['id'] in item:
            break
    assert minion['id'] in master.salt_key(minion['id'])['minions_pre']


def accept(master, minion):
    master.salt_key_accept(minion['id'])
    tag = "salt/minion/{0}/start".format(minion['id'])
    master['container'].run(
        'salt-run state.event tagmatch="{0}" count=1'.format(tag))
    assert minion['id'] in master.salt_key(minion['id'])['minions']


@pytest.fixture(scope="module")
def master(request, master_container):
    return MasterFactory(container=master_container)


@pytest.fixture
def minion_container(request, salt_root, minion_container_extras, salt_minion_config):
    fake = Faker()
    image = request.config.getini('MINION_IMAGE') or request.config.getini('IMAGE')
    obj = ContainerFactory(
        config__name='minion_{0}_{1}'.format(fake.word(), fake.word()),
        config__image=image,
        config__salt_config__tmpdir=salt_root,
        config__salt_config__conf_type='minion',
        config__salt_config__config={
            'base_config': salt_minion_config
        },
        **minion_container_extras
    )
    request.addfinalizer(obj.remove)
    return obj


@pytest.fixture()
def minion(request, master, minion_container):
    start = time.time()
    minion_obj = MinionFactory(container=minion_container)
    logger.info(
        "Time to container start: %s [including minion start]" % (time.time() - start)
    )
    wait_cached(master, minion_obj)
    logger.info("Time to key cache: %s [minion key in 'Unaccepted keys']" % (time.time() - start))
    accept(master, minion_obj)
    logger.info("Time to accept event: %s [minion key moved to 'Accepted keys']" % (time.time() - start))
    return minion_obj


@pytest.mark.parametrize('idx', range(10))
def test_ping(master, minion, idx):
    assert master.salt(minion['id'], "test.ping")[minion['id']] is True
