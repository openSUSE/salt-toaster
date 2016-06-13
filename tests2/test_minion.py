import pytest
import json
import yaml
import time
from factories import ContainerFactory, MasterFactory, MinionFactory


pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.fixture(scope="module")
def salt_master_config(master_root, file_root, pillar_root):
    config_file = master_root / 'master'
    config = {
        'hash_type': 'sha384',
        'pillar_roots': {
            'base': [pillar_root.strpath]
        },
        'file_roots': {
            'base': [file_root.strpath]
        }
    }
    config_file.write(yaml.safe_dump(config, default_flow_style=False))
    return dict(file=config_file, config=config)


@pytest.fixture(scope="module")
def salt_minion_config(master_container, minion_root):
    config_file = minion_root / 'minion'
    docker_client = master_container['docker_client']
    master_name = master_container['config']['name']
    data = docker_client.inspect_container(master_name)
    master_ip = data['NetworkSettings']['IPAddress']
    config = {
        'master': master_ip,
        'id': 'minime',
        'hash_type': 'sha384',
    }
    yaml_content = yaml.safe_dump(config, default_flow_style=False)
    config_file.write(yaml_content)
    return dict(file=config_file, config=config)


@pytest.fixture(scope="module")
def master_container(request, master_root, salt_master_config, docker_client):
    obj = ContainerFactory(
        config__salt_config__root=master_root, docker_client=docker_client)
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True)
    )
    return obj


@pytest.fixture(scope="module")
def minion_container(request, minion_root, salt_minion_config, docker_client):
    obj = ContainerFactory(
        config__salt_config__root=minion_root, docker_client=docker_client)
    request.addfinalizer(
        lambda: obj['docker_client'].remove_container(
            obj['config']['name'], force=True))
    return obj


@pytest.fixture(scope="module")
def master(request, master_container):
    return MasterFactory(container=master_container)


@pytest.fixture(scope="module")
def minion(request, minion_container):
    return MinionFactory(container=minion_container)


@pytest.fixture(scope='module')
def minion_key_cached(master):
    docker_client = master['container']['docker_client']
    master_name = master['container']['config']['name']
    SALT_KEY_CMD = "salt-key --output json"
    salt_key = docker_client.exec_create(master_name, cmd=SALT_KEY_CMD)
    time.sleep(10)
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert 'minime' in status['minions_pre']


@pytest.fixture(scope='module')
def minion_key_accepted(master, salt_minion_config, minion_key_cached):
    docker_client = master['container']['docker_client']
    master_name = master['container']['config']['name']
    minion_id = salt_minion_config['config']['id']
    CMD = "salt-key -a {0} -y --output json".format(minion_id)
    cmd_exec = docker_client.exec_create(master_name, cmd=CMD)
    docker_client.exec_start(cmd_exec['Id'])

    SALT_KEY_CMD = "salt-key --output json"
    salt_key = docker_client.exec_create(master_name, cmd=SALT_KEY_CMD)
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert minion_id in status['minions']
    time.sleep(3)


def test_ping_minion(master, salt_minion_config, minion_key_accepted):
    docker_client = master['container']['docker_client']
    master_name = master['container']['config']['name']
    minion_id = salt_minion_config['config']['id']
    CMD = "salt {minion_id} test.ping --output json".format(minion_id=minion_id)
    cmd_exec = docker_client.exec_create(master_name, cmd=CMD)
    output = docker_client.exec_start(cmd_exec['Id'])
    assert json.loads(output)[minion_id] is True


def test_pkg_list(master, salt_minion_config, minion_key_accepted):
    docker_client = master['container']['docker_client']
    master_name = master['container']['config']['name']
    minion_id = salt_minion_config['config']['id']
    CMD = "salt {minion_id} pkg.list_pkgs --output json".format(minion_id=minion_id)
    cmd_exec = docker_client.exec_create(master_name, cmd=CMD)
    output = docker_client.exec_start(cmd_exec['Id'])
    assert json.loads(output)[minion_id]
