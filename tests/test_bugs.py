import pytest


@pytest.fixture(scope='module')
def module_config(request):
    return {
        "masters": [
            {
                "config": {
                    'container__type': 'nspawn',
                    "container__config__image": 'master',
                    'container__config__salt_config__sls': {
                        'nscd': 'tests/sls/nscd.sls',
                    },
                },
                "minions": [
                    {
                        "config": {
                            "container__type": "nspawn",
                            "container__config__image": 'centos7_v2'
                        }
                    }
                ]
                "minions": [{}]
            }
        ]
    }


def test_bug_1027044(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    resp = master['fixture'].salt(minion['id'], 'state.apply nscd')
    assert resp[minion['id']]['service_|-service_nscd_|-nscd_|-dead']['result'] is True
    assert resp[minion['id']]['service_|-service_nscd_|-nscd_|-dead']['comment'] == (
        'The named service nscd is not available')
