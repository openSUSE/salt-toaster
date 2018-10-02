import os
import pytest
import time
import requests
from functools import partial


# RUN LIKE THIS: make suse.tests VERSION=sles12sp3 FLAVOR=products NOPULL=true SALT_TESTS=tests/test_batch_async.py


@pytest.fixture(scope='module')
def module_config(request, docker_client):
    return {
        "masters": [
            {
                "config": {
                    'container__config__salt_config__sls': [
                        'tests/sls/saltapi.sls',
                    ],
                    "container__config__host_config": docker_client.create_host_config(
                        binds={
                            os.getcwd(): {
                                'bind': "/salt-toaster/",
                                'mode': 'rw'
                            },
                            '/home/mdinca/store/repositories/salt': {
                                'bind': "/salt-devel/",
                                'mode': 'rw'
                            }
                        }
                    ),
                    "container__config__volumes": [
                        os.getcwd(),
                        '/home/mdinca/store/repositories/salt'
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
    master['container'].run('salt-call --local pkg.remove salt')
    master['container'].run('kill -9 $(pgrep salt-master)')
    master['container'].run('pip install -e /salt-devel')
    master['container'].run('pip install CherryPy rpdb')
    master['container'].run('salt-api -d')
    # Giving some time to salt-api to starting up.
    time.sleep(5)


def test_batch_async(salt_api_running, master, setup):
    endpoint = "http://{ip}:{port}/run".format(ip=master['container']['ip'], port='9080')
    batch_payload = {
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

    nobatch_payload = {
        'client': 'local_batch_async',
        'async': True,
        'tgt': '*',
        'fun': 'test.ping',
        'timeout': 3,
        'gather_job_timeout': 1,
        'username': 'admin',
        'password': 'admin',
        'eauth': 'auto',
        'batch': '2',
    }

    localasync_payload = {
        'client': 'local_async',
        'async': True,
        'tgt': '*',
        'fun': 'test.ping',
        'timeout': 3,
        'gather_job_timeout': 1,
        'username': 'admin',
        'password': 'admin',
        'eauth': 'auto',
    }

    haha = partial(
        master['container']['config']['client'].run,
        master['container']['config']['name'],
        '/bin/bash /salt-toaster/restart.sh')

    batch = partial(requests.post, endpoint, json=batch_payload)
    localasync = partial(requests.post, endpoint, json=localasync_payload)
    nobatch = partial(requests.post, endpoint, json=nobatch_payload)
    import pdb; pdb.set_trace()
