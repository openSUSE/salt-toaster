import pytest
from assertions import assert_proxyminion_key_state


pytestmark = pytest.mark.usefixtures("master")


def test_proxyminion_key_cached(env, proxyminion, wait_proxyminion_key_cached):
    assert_proxyminion_key_state(env, "unaccepted")
