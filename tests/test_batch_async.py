import pytest
import time
import requests
from functools import partial

@pytest.fixture(scope='module')
def module_config(request):
    return {
        "masters": [
            {
                "config": {
                    'container__config__salt_config__sls': [
                        'tests/sls/saltapi.sls',
                    ],
                    "container__config__salt_config__extra_configs": {
                        "salt_api_config": {
                            "rest_cherrypy": {
                                "port": 9080,
                                "host": "0.0.0.0",
                                "collect_stats": False,
                                "disable_ssl": True,
                            },
                            "external_auth": {
                                "auto": {
                                    "admin": ['.*', '@wheel', '@runner', '@jobs']
                                },
                            },
                        },
                    },
                },
                "minions": [{}, {}]
            }
        ]
    }


@pytest.fixture()
def salt_api_running(master):
    master['container'].run('salt-call --local pkg.refresh_db')
    master['container'].run('salt-call --local pkg.install salt-api')
    master['container'].run('salt-api -d')
    # Giving some time to salt-api to starting up.
    time.sleep(5)


def test_batch_async(salt_api_running, master):
    endpoint = "http://{ip}:{port}/run".format(ip=master['container']['ip'], port='9080')
    payload = {
        'client': 'local_batch',
        'tgt': '*',
        'fun': 'test.ping',
        'timeout': 3,
        'gather_job_timeout': 1,
        'username': 'admin',
        'password': 'admin',
        'eauth': 'auto',
        'batch': '1',
    }
    import pdb; pdb.set_trace()

    response = requests.post(endpoint, json=payload)
