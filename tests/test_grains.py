import json
import pytest


pytestmark = pytest.mark.usefixtures("platform_required", "master", "minion_key_accepted")


def check_os_release(minion):
    output = minion['container'].run("python tests/scripts/check_os_release.py")
    if not json.loads(output)['exists']:
        pytest.skip("/etc/os-release missing")


def test_get_cpuarch(minion):
    assert minion.salt_call('grains.get', 'cpuarch') == 'x86_64'


@pytest.mark.platform('sles')
def test_get_os_sles(minion):
    assert minion.salt_call('grains.get', 'os') == "SUSE"


@pytest.mark.platform('rhel')
def test_get_os_rhel(minion):
    assert minion.salt_call('grains.get', 'os') == "RedHat"


def test_get_items(minion):
    assert minion.salt_call('grains.get', 'items') == ''


@pytest.mark.platform('sles')
def test_get_os_family_sles(minion):
    assert minion.salt_call('grains.get', 'os_family') == 'Suse'


@pytest.mark.platform('rhel')
def test_get_os_family_rhel(minion):
    assert minion.salt_call('grains.get', 'os_family') == 'RedHat'


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


@pytest.mark.platform('sles')
def test_get_osrelease_info_sles(minion):
    suse_release = minion['container'].get_suse_release()
    major = suse_release['VERSION']
    minor = suse_release['PATCHLEVEL']
    expected = [major, minor] if minor else [major]
    assert minion.salt_call('grains.get', 'osrelease_info') == expected
