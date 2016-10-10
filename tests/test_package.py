import yaml
import json
import crypt
from functools import partial
from config import WHEEL_CONFIG
import pytest
from saltcontainers.factories import ContainerFactory


def pytest_generate_tests(metafunc):
    functions = [
        'test_master_shipped_with_sha256',
        'test_minion_shipped_with_sha256',
    ]
    if metafunc.function.func_name in functions:
        images = [metafunc.config.getini('IMAGE')]
        minion_image = metafunc.config.getini('MINION_IMAGE')
        if minion_image:
            images.append(minion_image)
        metafunc.parametrize('container', images, indirect=['container'])


@pytest.fixture(scope="module")
def container(request, docker_client):
    obj = ContainerFactory(
        config__docker_client=docker_client,
        config__image=request.param,
        config__salt_config=None,
        config__volumes=None,
        config__host_config=None
    )
    request.addfinalizer(obj.remove)
    return obj


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
def master_container_extras():
    return dict(config__environment=dict(PYTHONPATH='/salt-toaster'))


@pytest.mark.skiptags('devel', 'leap')
def test_master_shipped_with_sha256(container):
    """
    Test the Master is *shipped* with hash type set to SHA256.
    """
    master_config = container.run('cat /etc/salt/master')
    content = yaml.load(master_config)
    assert content['hash_type'] == 'sha256'


@pytest.mark.skiptags('devel', 'leap')
def test_minion_shipped_with_sha256(container):
    """
    Test the Minion is *shipped* with hash type set to SHA256.
    """
    minion_config = container.run('cat /etc/salt/minion')
    content = yaml.load(minion_config)
    assert content['hash_type'] == 'sha256'


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
