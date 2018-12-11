import os
import pytest
import time
from functools import partial


# RUN LIKE THIS: make suse.tests VERSION=sles12sp3 FLAVOR=products NOPULL=true SALT_TESTS=tests/test_workshop.py


@pytest.fixture(scope='module')
def module_config(request, docker_client):
    return {
        "masters": [
            {
                "config": {
                    'container__config__salt_config__apply_states': [
                        'tests/sls/top.sls',
                        'tests/sls/saltapi.sls',
                    ],
                    "container__config__host_config": docker_client.create_host_config(
                        binds={
                            os.getcwd(): {
                                'bind': "/salt-toaster/", 'mode': 'rw'
                            },
                            '/home/mdinca/store/repositories/salt': {
                                'bind': "/salt-devel/", 'mode': 'rw'
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
                "minions": [
                    {'config': {
                        'container__config__salt_config__id': 'rhel7',
                        "container__config__image": (
                            "registry.mgr.suse.de/toaster-rhel7-products"
                        )
                    }},
                    {'config': {
                        'container__config__salt_config__id': 'rhel6',
                        "container__config__image": (
                            "registry.mgr.suse.de/toaster-rhel6-products"
                        )
                    }},
                    {'config': {
                        'container__config__salt_config__id': 'sles11sp3',
                        "container__config__image": (
                            "registry.mgr.suse.de/toaster-sles11sp3-products"
                        )
                    }},
                    {'config': {
                        'container__config__salt_config__id': 'sles12sp3',
                        "container__config__image": (
                            "registry.mgr.suse.de/toaster-sles12sp3-products"
                        )
                    }},
                    {'config': {
                        'container__config__salt_config__id': 'sles15',
                        "container__config__image": (
                            "registry.mgr.suse.de/toaster-sles15-products-testing"
                        )
                    }},
                ]
            }
        ]
    }


@pytest.fixture()
def salt_api_running(master):
    master['container'].run('salt-call --local pkg.refresh_db')
    master['container'].run('salt-call --local pkg.remove salt')
    master['container'].run('kill -9 $(pgrep salt-master)')
    master['container'].run('pip install --no-deps -e /salt-devel')
    master['container'].run('pip install CherryPy rpdb epdb')
    master['container'].run('salt-api -d')
    master['container'].run('ln -s /salt-toaster/.bashrc /root/.bashrc')
    # Giving some time to salt-api to starting up.
    time.sleep(5)


def test_workshop(salt_api_running, master, setup):
    import pdb; pdb.set_trace()
