import yaml


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
