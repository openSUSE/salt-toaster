import pytest


@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                'config': {
                    'container__config__salt_config__sls': {
                        'latest': 'tests/sls/latest.sls',
                        'latest-again': 'tests/sls/latest-again.sls'
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
