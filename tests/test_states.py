import pytest
import os


@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                'config': {
                    'container__config__salt_config__sls': {
                        'latest': 'tests/sls/latest.sls',
                        'latest-again': 'tests/sls/latest-again.sls',
                        'downloaded': 'tests/sls/downloaded.sls',
                        'patches-downloaded': 'tests/sls/patches-downloaded.sls'
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


def test_pkg_downloaded(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    list_pkgs_pre = master['fixture'].salt(minion['id'], 'pkg.list_downloaded')
    resp = master['fixture'].salt(minion['id'], 'state.apply downloaded')
    list_pkgs_post = master['fixture'].salt(minion['id'], 'pkg.list_downloaded')
    assert resp[minion['id']][
        'pkg_|-test-pkg-downloaded_|-test-package_|-downloaded']['result'] is True
    assert list_pkgs_pre == list_pkgs_post


def test_patches_downloaded(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    patches = master['fixture'].salt(minion['id'],
        'pkg.list_patches'
        )[minion['id']].encode('utf-8').split(os.linesep)
    patches = filter(lambda x: not x['installed'], patches)[:2]
    if not patches:
        pytest.xfail('No advisory patches are available to downloaded')
    list_pkgs_pre = master['fixture'].salt(minion['id'], 'pkg.list_downloaded')
    resp = master['fixture'].salt(minion['id'], 'state.apply patches-downloaded pillar=\'{0}\''.format(patches))
    list_pkgs_post = master['fixture'].salt(minion['id'], 'pkg.list_downloaded')
    assert resp[minion['id']]['pkg_|-test-patches-downloaded_|-test-patches-downloaded_|-patch_downloaded']['result'] is True
    assert list_pkgs_pre != list_pkgs_post


def test_patches_installed(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    patches = master['fixture'].salt(minion['id'],
        'pkg.list_patches'
        )[minion['id']].encode('utf-8').split(os.linesep)
    patches = filter(lambda x: not x['installed'], patches)[:2]
    if not patches:
        pytest.xfail('No advisory patches are available to install')
    list_pkgs_pre = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    resp = master['fixture'].salt(minion['id'], 'state.apply patches-installed pillar=\'{0}\''.format(patches))
    list_pkgs_post = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    assert resp[minion['id']]['pkg_|-test-patches-installed_|-test-patches-installed_|-patch_installed']['result'] is True
    assert list_pkgs_pre != list_pkgs_post
