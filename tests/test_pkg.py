import re
import pytest


pytestmark = pytest.mark.usefixtures("master", "minion", "minion_key_accepted")


@pytest.mark.tags_xfail('rhel')
def test_pkg_list_updates(minion):
    res = minion.salt_call('pkg.list_updates', 'test-package')
    assert res['test-package'].startswith('42:0.1-')


@pytest.mark.tags_xfail('rhel')
def test_pkg_info_available(minion):
    res = minion.salt_call('pkg.info_available', 'test-package')
    assert res['test-package']['summary'] == "Test package for Salt's pkg.info_installed"
    assert re.match(
        "out-of-date \(version 42:0.0-.+ installed\)",
        res['test-package']['status'])


@pytest.mark.tags_xfail('rhel')
def test_pkg_info_installed(minion):
    res = minion.salt_call('pkg.info_installed', 'test-package')
    assert res['test-package']['vendor'] == "obs://build.opensuse.org/systemsmanagement"


@pytest.mark.tags_xfail('rhel')
def test_pkg_info_installed_epoch(minion):
    res = minion.salt_call('pkg.info_installed', 'test-package')
    assert res['test-package']['epoch'] == "42"


@pytest.mark.tags('sles')
def test_grains_items_sles(minion):
    res = minion.salt_call('grains.items', 'test-package')
    assert res['os_family'] == "Suse"
    assert res['kernel'] == "Linux"
    assert res['cpuarch'] == "x86_64"


@pytest.mark.tags('rhel')
def test_grains_items_rhel(minion):
    res = minion.salt_call('grains.items', 'test-package')
    assert res['os_family'] == "RedHat"
    assert res['kernel'] == "Linux"
    assert res['cpuarch'] == "x86_64"
