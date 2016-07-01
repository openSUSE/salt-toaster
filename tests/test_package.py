import yaml
import json
import crypt
from functools import partial
from config import WHEEL_CONFIG
import pytest
from faker import Faker
from saltcontainers.factories import ContainerFactory


@pytest.fixture(scope="module")
def container(request, docker_client):
    obj = ContainerFactory(
        docker_client=docker_client,
        config__salt_config=None,
        config__volumes=None,
        config__host_config=None
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


def test_master_shipped_with_sha256(container):
    """
    Test the Master is *shipped* with hash type set to SHA256.
    """
    master_config = container.run('cat /etc/salt/master')
    content = yaml.load(master_config)
    assert content['hash_type'] == 'sha256'


def test_minion_shipped_with_sha256(container):
    """
    Test the Minion is *shipped* with hash type set to SHA256.
    """
    minion_config = container.run('cat /etc/salt/minion')
    content = yaml.load(minion_config)
    assert content['hash_type'] == 'sha256'


@pytest.fixture(scope="module")
def salt_master_config(file_root, pillar_root):
    return {
        'base_config': {
            'hash_type': 'sha384',
            'pillar_roots': {
                'base': [pillar_root]
            },
            'file_roots': {
                'base': [file_root]
            },
            'external_auth': {
                'pam': {
                    WHEEL_CONFIG['user']: ['@wheel']
                }
            }
        }
    }


@pytest.fixture(scope="module")
def master_container(request, salt_root, salt_master_config, docker_client):
    fake = Faker()
    obj = ContainerFactory(
        config__name='master_{0}_{1}'.format(fake.word(), fake.word()),
        config__salt_config__tmpdir=salt_root,
        docker_client=docker_client,
        config__salt_config__conf_type='master',
        config__salt_config__config=salt_master_config,
        config__salt_config__post__id='{0}_{1}'.format(fake.word(), fake.word()),
        config__environment=dict(PYTHONPATH='/salt-toaster')
    )
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


def test_hash_type_is_used(request, master, salt_master_config):
    user = WHEEL_CONFIG['user']
    password_salt = '00'
    password = crypt.crypt(WHEEL_CONFIG['password'], password_salt)
    request.addfinalizer(
        partial(master['container'].run, "userdel {0}".format(user)))
    master['container'].run("useradd {0} -p '{1}'".format(user, password))
    raw_output = master['container'].run(
        "python tests/scripts/wheel_config_values.py"
    )
    output = json.loads(raw_output)
    expected = salt_master_config['base_config']['hash_type']
    assert output['data']['return']['hash_type'] == expected
