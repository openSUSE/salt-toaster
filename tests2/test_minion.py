import pytest
import json


pytestmark = pytest.mark.usefixtures("master", "minion")


STATES_MAPPING = dict(unaccepted='minions_pre', accepted='minions')


@pytest.fixture(scope="module")
def salt_key(docker_client):
    SALT_KEY_CMD = "salt-key --output json"
    return docker_client.exec_create('master', cmd=SALT_KEY_CMD)


def test_minion_key_cached(env, context, salt_key, docker_client, wait_minion_key_cached):
    output = docker_client.exec_start(salt_key['Id'])
    status = json.loads(output)
    assert context['minion_id'] in status['minions_pre']
