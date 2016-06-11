import pytest
import json


pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.fixture()
def salt_key(docker_client):
    SALT_KEY_CMD = "salt-key --output json"
    return docker_client.exec_create('master', cmd=SALT_KEY_CMD)


def test_minion_key_cached(context, salt_key, docker_client, wait_minion_key_cached):
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert context['minion']['salt']['id'] in status['minions_pre']


def test_minion_key_accepted(context, salt_key, docker_client, wait_minion_key_cached):
    minion_id = context['minion']['salt']['id']
    CMD = "salt-key -a {0} -y --output json".format(minion_id)
    cmd_exec = docker_client.exec_create(
        context['master']['container']['name'], cmd=CMD)
    docker_client.exec_start(cmd_exec['Id'])

    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert minion_id in status['minions']
