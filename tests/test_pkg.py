import re
import pytest
import datetime
from functools import partial

pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.mark.xfailtags('rhel', 'leap')
def test_pkg_list_updates(minion):
    res = minion.salt_call('pkg.list_updates', 'test-package')
    assert res['test-package'].startswith('42:0.1-')


@pytest.mark.xfailtags('rhel', 'leap')
def test_pkg_info_available(minion):
    res = minion.salt_call('pkg.info_available', 'test-package')
    assert res['test-package']['summary'] == "Test package for Salt's pkg.info_installed"
    assert re.match(
        "out-of-date \(version 42:0.0-.+ installed\)",
        res['test-package']['status'])


def test_pkg_info_installed(minion):
    res = minion.salt_call('pkg.info_installed', 'test-package')
    assert res['test-package']['vendor'] == "obs://build.opensuse.org/systemsmanagement"


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


@pytest.fixture
def timezone(request, minion):
    tz = "Europe/Berlin"
    out = minion['container'].run(
        'ln -sf /usr/share/zoneinfo/{} /etc/localtime'.format(tz))
    def finalizer(minion):
        minion["container"].run("rm -f /etc/localtime")
        minion["container"].run("ln -sf /usr/share/zoneinfo/UTC /etc/localtime")
    request.addfinalizer(partial(finalizer, minion))


@pytest.mark.tags('sles12sp2')
def test_salt_upgrade(minion):
    ex = minion["container"].run
    ex("rm /etc/zypp/repos.d/salt.repo")
    ex("zypper --non-interactive rm salt salt-minion")
    ex("/usr/bin/cp /salt-toaster/tests/sysconfigs/salt-products.repo /etc/zypp/repos.d/")
    ex("zypper --non-interactive in salt-minion")
    ex("rm /etc/zypp/repos.d/salt-products.repo")
    ex("/usr/bin/cp /salt-toaster/tests/sysconfigs/salt-next.repo /etc/zypp/repos.d/")
    ex("zypper ref")
    minion.stop()
    ex("zypper --non-interactive up salt-minion")
    ex("cp /etc/salt/minion.rpmsave /etc/salt/minion")
    minion.start()

    import time
    time.sleep(5)
    assert minion.salt_call('test.ping')


@pytest.mark.xfail
def test_pkg_info_install_date(minion, timezone):
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
