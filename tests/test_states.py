import yaml
import time
import pytest
from faker import Faker
from saltcontainers.factories import MinionFactory, MasterFactory


@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                'config': {
                    'container__config__salt_config__sls': {
                        'oldest': {
                            'oldest-version': {
                                'pkg.installed': [
                                    {
                                        'name': 'test-package',
                                        'version': '42:0.0-3.1'
                                    }
                                ]
                            }
                        },
                        'latest': {
                            'include': ['oldest'],
                            'latest-version': {
                                'pkg.latest': [
                                    {'name': 'test-package'},
                                    {'require': [{'pkg': 'oldest-version'}]}
                                ]
                            },
                        },
                        'latest-again': {
                            'include': ['latest'],
                            'latest-version-again': {
                                'pkg.latest': [
                                    {'name': 'test-package'},
                                    {'require': [{'pkg': 'latest-version'}]}
                                ]
                            }
                        }
                    }
                },
                'minions': [{'config': {}}, {'config': {}}]
            }
        ]
    }


def test_pkg_latest_version(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    resp = master['fixture'].salt(minion['id'], 'state.apply latest')
    assert resp[minion['id']][
        'pkg_|-latest-version_|-test-package_|-latest']['result'] is True


def test_pkg_latest_version_already_installed(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][1]
    resp = master['fixture'].salt(minion['id'], 'state.apply latest-again')
    assert resp[minion['id']][
        'pkg_|-latest-version_|-test-package_|-latest']['result'] is True
