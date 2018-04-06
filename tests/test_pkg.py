import re
import pytest
import datetime
from utils import retry
from functools import partial

pytestmark = pytest.mark.usefixtures("master", "minion")


def _pkg_list_updates(minion):
    try:
        res = minion.salt_call('pkg.list_updates', 'test-package')
        return res['test-package'].startswith('42:0.1-')
    except TypeError:
        return False


@pytest.mark.xfailtags('rhel', 'leap')
def test_pkg_list_updates(minion):
    res = minion.salt_call('pkg.list_updates', 'test-package')
    assert retry(partial(_pkg_list_updates, minion))


def _pkg_info_available(minion):
    try:
        return minion.salt_call('pkg.info_available', 'test-package')
    except TypeError:
        return False


def _pkg_info_available_dos(func):
    res = func()
    assert res
    assert 'test-package' in res
    assert res['test-package']['summary'] == "Test package for Salt's pkg.info_installed"
    assert re.match(
        "out-of-date \(version 42:0.0-.+ installed\)",
        res['test-package']['status'])
    return True


@pytest.mark.xfailtags('rhel', 'leap')
def test_pkg_info_available(minion):
    assert retry(partial(_pkg_info_available, minion), definition_of_success=_pkg_info_available_dos)


def test_pkg_info_installed(request, minion):
    minion.salt_call('pkg.install', 'test-package')
    request.addfinalizer(
        partial(minion.salt_call, 'pkg.remove', 'test-package'))
    res = minion.salt_call('pkg.info_installed', 'test-package')
    assert res['test-package']['vendor'] == "obs://build.opensuse.org/systemsmanagement"


def test_pkg_info_installed_epoch(request, minion):
    minion.salt_call('pkg.install', 'test-package')
    request.addfinalizer(
        partial(minion.salt_call, 'pkg.remove', 'test-package'))
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


@pytest.fixture
def timezone(request, minion):
    tz = "Europe/Berlin"
    out = minion['container'].run(
        'ln -sf /usr/share/zoneinfo/{} /etc/localtime'.format(tz))
    def finalizer(minion):
        minion["container"].run("rm -f /etc/localtime")
        minion["container"].run("ln -sf /usr/share/zoneinfo/UTC /etc/localtime")
    request.addfinalizer(partial(finalizer, minion))


@pytest.mark.xfail
def test_pkg_info_install_date(request, minion, timezone):
    minion.salt_call('pkg.install', 'test-package')
    request.addfinalizer(
        partial(minion.salt_call, 'pkg.remove', 'test-package'))
    request.addfinalizer(
        partial(minion.salt_call, 'pkg.remove', 'test-package'))
    res = minion.salt_call('pkg.info_installed', 'test-package')
    dt = datetime.datetime.strptime(
        res['test-package']['install_date'], "%Y-%m-%dT%H:%M:%SZ")
    timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
    assert int(timestamp) == int(res['test-package']['install_date_time_t'])


@pytest.mark.xfail
def test_pkg_info_build_date(minion, timezone):
    res = minion.salt_call('pkg.info_installed', 'test-package')
    dt = datetime.datetime.strptime(
        res['test-package']['build_date'], "%Y-%m-%dT%H:%M:%SZ")
    timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
    assert int(timestamp) == int(res['test-package']['build_date_time_t'])


def test_pkg_install_downloadonly(request, minion):
    list_pkgs_pre = minion.salt_call('pkg.list_downloaded')
    res = minion.salt_call('pkg.install', 'test-package downloadonly=True')
    request.addfinalizer(
        partial(minion.salt_call, 'pkg.remove', 'test-package'))
    list_pkgs_post = minion.salt_call('pkg.list_downloaded')
    assert list_pkgs_pre != list_pkgs_post
    assert 'test-package' in res
    assert 'test-package' not in list_pkgs_pre
    assert 'test-package' in list_pkgs_post
