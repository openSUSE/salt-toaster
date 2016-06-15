import time
import json
import pytest
from faker import Faker
from factories import ContainerFactory


pytestmark = pytest.mark.usefixtures("master", "minion_key_accepted")


def check_os_release(minion):
    output = minion['container'].run("python tests2/scripts/check_os_release.py")
    if not json.loads(output)['exists']:
        pytest.skip("/etc/os-release missing")


@pytest.fixture(scope="module")
def minion_config():
    fake = Faker()
    return {'id': u'{0}_{1}'.format(fake.word(), fake.word())}


@pytest.fixture(scope="module")
def salt_master_config(salt_root, file_root, pillar_root, docker_client):
    fake = Faker()
    return dict(
        config__name='master_{0}_{1}'.format(fake.word(), fake.word()),
        config__salt_config__tmpdir=salt_root,
        config__salt_config__conf_type='master',
        config__salt_config__config={
            'base_config': {
                'pillar_roots': {'base': [pillar_root]},
                'file_roots': {'base': [file_root]}
            }
        },
        config__salt_config__post__id='{0}_{1}'.format(fake.word(), fake.word())
    )


@pytest.fixture(scope="module")
def salt_minion_config(salt_root, master_container, minion_config):
    return dict(
        config__name='minion_' + minion_config['id'],
        config__salt_config__tmpdir=salt_root,
        config__salt_config__conf_type='minion',
        config__salt_config__config={
            'base_config': {
                'master': master_container['ip'],
            }
        },
        config__salt_config__post__id=minion_config['id']
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


@pytest.fixture(scope='module')
def minion_key_accepted(master, minion, minion_config):
    time.sleep(10)
    assert minion_config['id'] in master.salt_key(minion_config['id'])['minions_pre']
    master.salt_key_accept(minion_config['id'])
    assert minion_config['id'] in master.salt_key()['minions']
    time.sleep(5)


def test_get_cpuarch(minion):
    assert minion.salt_call('grains.get', 'cpuarch') == 'x86_64'


def test_get_os(minion):
    assert minion.salt_call('grains.get', 'os') == "SUSE"


def test_get_items(minion):
    assert minion.salt_call('grains.get', 'items') == ''


def test_get_os_family(minion):
    assert minion.salt_call('grains.get', 'os_family') == 'Suse'


def test_get_oscodename(minion):
    check_os_release(minion)
    os_release = minion['container'].get_os_release()
    assert minion.salt_call('grains.get', 'oscodename') == os_release['PRETTY_NAME']


def test_get_osfullname(minion):
    check_os_release(minion)
    os_release = minion['container'].get_os_release()
    assert minion.salt_call('grains.get', 'osfullname') == os_release['NAME']


def test_get_osarch(minion):
    expected = minion['container'].run(['rpm', '--eval', '%{_host_cpu}']).strip()
    assert minion.salt_call('grains.get', 'osarch') == expected


def test_get_osrelease(minion):
    check_os_release(minion)
    os_release = minion['container'].get_os_release()
    assert minion.salt_call('grains.get', 'osrelease') == os_release['VERSION_ID']


def test_get_osrelease_info(minion):
    suse_release = minion['container'].get_suse_release()
    major = suse_release['VERSION']
    minor = suse_release['PATCHLEVEL']
    expected = [major, minor] if minor else [major]
    assert minion.salt_call('grains.get', 'osrelease_info') == expected
