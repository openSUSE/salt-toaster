import pytest


pytestmark = pytest.mark.usefixtures("master", "minion")


STATES_MAPPING = dict(unaccepted='minions_pre', accepted='minions')


def assert_minion_key_state(env, minion_id, wheel_client, expected_state):
    assert expected_state in STATES_MAPPING
    status = wheel_client.cmd_sync(
        dict(
            fun='key.list_all',
            eauth="pam",
            username=env['CLIENT_USER'],
            password=env['CLIENT_PASSWORD']
        )
    )
    print('{0} in {1}'.format(env['HOSTNAME'], STATES_MAPPING[expected_state]))
    assert minion_id in status['data']['return'][STATES_MAPPING[expected_state]]


def test_minion_key_cached(env, context, wheel_client, wait_minion_key_cached):
    assert_minion_key_state(env, context['minion_id'], wheel_client, "unaccepted")


def test_minion_key_accepted(env, context, wheel_client, accept_minion_key):
    assert_minion_key_state(env, context['minion_id'], wheel_client, "accepted")
