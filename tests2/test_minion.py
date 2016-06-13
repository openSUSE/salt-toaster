import pytest
import json
import time


pytestmark = pytest.mark.usefixtures("master", "minion")


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
def minion_key_accepted(master, minion_key_cached):
    docker_client = master['container']['docker_client']
    master_name = master['container']['config']['name']
    minion_id = 'minime'
    CMD = "salt-key -a {0} -y --output json".format(minion_id)
    cmd_exec = docker_client.exec_create(master_name, cmd=CMD)
    docker_client.exec_start(cmd_exec['Id'])

    SALT_KEY_CMD = "salt-key --output json"
    salt_key = docker_client.exec_create(master_name, cmd=SALT_KEY_CMD)
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert minion_id in status['minions']
    time.sleep(3)


def test_ping_minion(master, minion_key_accepted):
    docker_client = master['container']['docker_client']
    master_name = master['container']['config']['name']
    minion_id = 'minime'
    CMD = "salt {minion_id} test.ping --output json".format(minion_id=minion_id)
    cmd_exec = docker_client.exec_create(master_name, cmd=CMD)
    output = docker_client.exec_start(cmd_exec['Id'])
    assert json.loads(output)[minion_id] is True
