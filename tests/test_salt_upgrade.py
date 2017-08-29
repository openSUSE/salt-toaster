import pytest


pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.mark.timeout(300)
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
