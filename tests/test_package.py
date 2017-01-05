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


@pytest.fixture(scope='module')
def module_config(request):
    return {"masters": [
        {
            "config": {
                "container__config__environment": {
                    "PYTHONPATH": "/salt-toaster"},
                "container__config__salt_config__extra_configs": {
                    "external_auth": {
                        "external_auth": {
                            "pam": {WHEEL_CONFIG["user"]: ["@wheel"]}
                        }
                    },
                    "hashtype": {"hash_type": "sha384"}
                }
            }
        }
    ]}


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


@pytest.mark.tags('products', 'products-testing')
def test_master_shipped_with_sha256(container):
    """
    Test the Master is *shipped* with hash type set to SHA256.
    """
    master_config = container.run('cat /etc/salt/master')
    content = yaml.load(master_config)
    assert content['hash_type'] == 'sha256'


@pytest.mark.tags('products', 'products-testing')
def test_minion_shipped_with_sha256(container):
    """
    Test the Minion is *shipped* with hash type set to SHA256.
    """
    minion_config = container.run('cat /etc/salt/minion')
    content = yaml.load(minion_config)
    assert content['hash_type'] == 'sha256'


def test_hash_type_is_used(request, master):
    user = WHEEL_CONFIG['user']
    password_salt = '00'
    password = crypt.crypt(WHEEL_CONFIG['password'], password_salt)
    request.addfinalizer(
        partial(master['container'].run, "userdel {0}".format(user)))
    master['container'].run("useradd {0} -p '{1}'".format(user, password))
    raw_output = master['container'].run(
        "python tests/scripts/wheel_config_values.py")
    output = json.loads(raw_output)
    assert output['data']['return']['hash_type'] == "sha384"
