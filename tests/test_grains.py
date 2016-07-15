import json
import pytest


pytestmark = pytest.mark.usefixtures("master", "minion_key_accepted")


def test_get_cpuarch(minion):
    assert minion.salt_call('grains.get', 'cpuarch') == 'x86_64'


@pytest.mark.tags('sles')
def test_get_os_sles(minion):
    assert minion.salt_call('grains.get', 'os') == "SUSE"


@pytest.mark.tags('rhel')
def test_get_os_rhel(minion):
    assert minion.salt_call('grains.get', 'os') == "RedHat"


def test_get_items(minion):
    assert minion.salt_call('grains.get', 'items') == ''


@pytest.mark.tags('sles')
def test_get_os_family_sles(minion):
    assert minion.salt_call('grains.get', 'os_family') == 'Suse'


@pytest.mark.tags('rhel')
def test_get_os_family_rhel(minion):
    assert minion.salt_call('grains.get', 'os_family') == 'RedHat'


@pytest.mark.tags('rhel', 'sles11sp4', 'sles12', 'sles12sp1')
def test_get_oscodename(minion):
    os_release = minion['container'].get_os_release()
    assert minion.salt_call('grains.get', 'oscodename') == os_release['PRETTY_NAME']


@pytest.mark.tags('rhel', 'sles11sp4', 'sles12', 'sles12sp1')
def test_get_osfullname(minion):
    os_release = minion['container'].get_os_release()
    assert minion.salt_call('grains.get', 'osfullname') == os_release['NAME']


def test_get_osarch(minion):
    expected = minion['container'].run(['rpm', '--eval', '%{_host_cpu}']).strip()
    assert minion.salt_call('grains.get', 'osarch') == expected


@pytest.mark.tags('rhel', 'sles11sp4', 'sles12', 'sles12sp1')
def test_get_osrelease(minion):
    os_release = minion['container'].get_os_release()
    assert minion.salt_call('grains.get', 'osrelease') == os_release['VERSION_ID']


@pytest.mark.tags('sles')
def test_get_osrelease_info_sles(minion):
    suse_release = minion['container'].get_suse_release()
    major = suse_release['VERSION']
    minor = suse_release['PATCHLEVEL']
    expected = [major, minor] if minor else [major]
    assert minion.salt_call('grains.get', 'osrelease_info') == expected
