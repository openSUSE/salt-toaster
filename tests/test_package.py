import os
import yaml
import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get('DEVEL') == 'true',
    reason="Not possible to test package with DEVEL=true")


def test_master_shipped_with_sha256():
    """
    Test the Master is *shipped* with hash type set to SHA256.
    """
    with open('/etc/salt/master', 'rb') as master_config:
        content = yaml.load(master_config)
        assert content['hash_type'] == 'sha256'


def test_minion_shipped_with_sha256():
    """
    Test the Minion is *shipped* with hash type set to SHA256.
    """
    with open('/etc/salt/minion', 'rb') as master_config:
        content = yaml.load(master_config)
        assert content['hash_type'] == 'sha256'


def test_sha256_is_used(master, env, wheel_client):
    out = wheel_client.cmd_sync(
        dict(
            fun='config.values',
            eauth="pam",
            username=env['CLIENT_USER'],
            password=env['CLIENT_PASSWORD']
        )
    )
    assert out['data']['return']['hash_type'] == env['HASH_TYPE']
