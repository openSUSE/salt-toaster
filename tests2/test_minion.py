import pytest
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
def minion_key_cached(master, salt_minion_config):
    time.sleep(10)
    minion_id = salt_minion_config['config']['id']
    assert minion_id in master.salt_key(minion_id)['minions_pre']


@pytest.fixture(scope='module')
def minion_key_accepted(master, minion, salt_minion_config, minion_key_cached):
    minion_id = salt_minion_config['config']['id']
    master.salt_key_accept(minion_id)
    assert minion_id in master.salt_key()['minions']
    time.sleep(5)


def test_ping_minion(master, minion, salt_minion_config, minion_key_accepted):
    minion_id = salt_minion_config['config']['id']
    assert master.salt(minion_id, "test.ping")[minion_id] is True


def test_pkg_list(minion, minion_key_accepted):
    assert minion.salt_call("pkg.list_pkgs")['local']
