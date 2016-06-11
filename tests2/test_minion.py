import pytest
import json
import time


pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.fixture(scope='module')
def minion_key_cached(context, docker_client):
    SALT_KEY_CMD = "salt-key --output json"
    salt_key = docker_client.exec_create('master', cmd=SALT_KEY_CMD)
    time.sleep(10)
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert context['minion']['salt']['id'] in status['minions_pre']


@pytest.fixture(scope='module')
def minion_key_accepted(context, docker_client, minion_key_cached):
    minion_id = context['minion']['salt']['id']
    CMD = "salt-key -a {0} -y --output json".format(minion_id)
    cmd_exec = docker_client.exec_create(
        context['master']['container']['name'], cmd=CMD)
    docker_client.exec_start(cmd_exec['Id'])

    SALT_KEY_CMD = "salt-key --output json"
    salt_key = docker_client.exec_create('master', cmd=SALT_KEY_CMD)
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert minion_id in status['minions']
    time.sleep(3)


def test_ping_minion(env, context, docker_client, minion_key_accepted):
    CMD = "salt {minion_id} test.ping --output json".format(
        minion_id=context['minion']['salt']['id'])
    cmd_exec = docker_client.exec_create(
        context['master']['container']['name'], cmd=CMD)
    output = docker_client.exec_start(cmd_exec['Id'])
    assert {context['minion']['salt']['id']: True} == json.loads(output)
