import yaml
import json
import crypt
from functools import partial
from config import WHEEL_CONFIG
import pytest
from saltcontainers.factories import ContainerFactory


def pytest_generate_tests(metafunc):
    functions = [
        'test_master_shipped_config',
        'test_minion_shipped_config',
    ]
    if metafunc.function.__name__ in functions:
        images = [metafunc.config.getini('IMAGE')]
        minion_image = metafunc.config.getini('MINION_IMAGE')
        if minion_image:
            images.append(minion_image)
        metafunc.parametrize('container', images, indirect=['container'])
    if 'python' in metafunc.fixturenames:
        tags = set(metafunc.config.getini('TAGS'))
        if 'sles15' in tags or 'sles15sp1' in tags:
            metafunc.parametrize("python", ["python3"])
        else:
            metafunc.parametrize("python", ["python"])


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
def container(request):
    obj = ContainerFactory(config__image=request.param, config__salt_config=None)
    request.addfinalizer(obj.remove)
    return obj


@pytest.mark.xfailtags('rhel')
def test_master_shipped_config(container):
    master_config = container.run('cat /etc/salt/master')
    content = yaml.load(master_config)
    assert content == {'user': 'salt', 'syndic_user': 'salt'}


def test_minion_shipped_config(container):
    minion_config = container.run('cat /etc/salt/minion')
    content = yaml.load(minion_config)
    assert content is None


def test_hash_type_is_used(request, master, python):
    user = WHEEL_CONFIG['user']
    password_salt = '00'
    password = crypt.crypt(WHEEL_CONFIG['password'], password_salt)
    request.addfinalizer(
        partial(master['container'].run, "userdel {0}".format(user)))
    master['container'].run("useradd {0} -p '{1}'".format(user, password))
    raw_output = master['container'].run(
        "{0} tests/scripts/wheel_config_values.py".format(python))
    output = json.loads(raw_output)
    assert output['data']['return']['hash_type'] == "sha384"
