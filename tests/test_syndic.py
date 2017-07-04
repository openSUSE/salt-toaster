import pytest
from utils import retry


pytestmark = pytest.mark.skip


@pytest.fixture(scope='module')
def masters(syndics, minions):
    return [
        {
            'config': {
                "container__config__salt_config__extra_configs": {
                    "syndic": {
                        "order_masters": True
                    },
                }
            },
            'syndics': syndics,
            'minions': [minions[0]]
        }
    ]


@pytest.fixture(scope='module')
def syndics(minions):
    return [
        {'minions': [minions[1], minions[2]]},
        {'minions': [minions[3], minions[4]]}
    ]


@pytest.fixture(scope='module')
def minions():
    return 5 * [{}]


@pytest.fixture(scope='module')
def module_config(masters):
    return {'masters': masters}


@pytest.mark.timeout(0)
def test_manage_status(setup, masters, syndics, minions):

    status = masters[0]['fixture'].salt_run('manage.status')

    assert syndics[0]['id'] in status['down']
    assert syndics[1]['id'] in status['down']

    assert minions[0]['id'] in status['up']
    assert minions[1]['id'] in status['up']
    assert minions[2]['id'] in status['up']
    assert minions[3]['id'] in status['up']
    assert minions[4]['id'] in status['up']
