import pytest


pytestmark = pytest.mark.usefixtures("master", "minion_ready")


def test_get_cpuarch(caller_client):
    assert caller_client.cmd('grains.get', 'cpuarch') == 'x86_64'
