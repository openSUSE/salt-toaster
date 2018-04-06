import pytest
import os
from functools import partial
from utils import retry


@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                'config': {
                    'container__config__salt_config__sls': [
                        'tests/sls/latest.sls',
                        'tests/sls/latest-again.sls',
                        'tests/sls/downloaded.sls',
                        'tests/sls/patches-downloaded.sls'
                    ]
                },
                'minions': [{'config': {}}, {'config': {}}]
            }
        ]
    }


def test_pkg_latest_version(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    def test(master, minion):
        try:
            resp = master['fixture'].salt(minion['id'], 'state.apply latest')
            assert resp
            assert minion['id'] in resp
            assert resp[minion['id']][
                'pkg_|-latest-version_|-test-package_|-latest']['result'] is True
            return True
        except TypeError:
            return False
    assert retry(partial(test, master, minion))


def test_pkg_latest_version_already_installed(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][1]
    def test(master, minion):
        try:
            resp = master['fixture'].salt(minion['id'], 'state.apply latest-again')
            assert resp
            assert minion['id'] in resp
            assert resp[minion['id']][
                'pkg_|-latest-version_|-test-package_|-latest']['result'] is True
            return True
        except TypeError:
            return False
    assert retry(partial(test, master, minion))


def test_pkg_installed_downloadonly(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    list_pkgs_pre = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    resp = master['fixture'].salt(minion['id'], 'state.apply downloaded')
    list_pkgs_post = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    assert resp[minion['id']][
        'pkg_|-test-pkg-downloaded_|-test-package_|-installed']['result'] is True
    assert list_pkgs_pre == list_pkgs_post


@pytest.mark.xfail
@pytest.mark.tags('sles')
def test_patches_installed_downloadonly_sles(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    patches = master['fixture'].salt(minion['id'],
        'cmd.run "zypper --quiet patches | cut -d\'|\' -f2 | cut -d\' \' -f2"'
        )[minion['id']].encode('utf-8').split(os.linesep)
    patches = {"patches": filter(lambda x: "SUSE-SLE-SERVER" in x, patches)[:2]}
    list_pkgs_pre = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    resp = master['fixture'].salt(minion['id'], 'state.apply patches-downloaded pillar=\'{0}\''.format(patches))
    list_pkgs_post = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    assert resp[minion['id']]['pkg_|-test-patches-downloaded_|-test-patches-downloaded_|-installed']['result'] is True
    assert list_pkgs_pre == list_pkgs_post


@pytest.mark.xfail
@pytest.mark.tags('rhel')
def test_patches_installed_downloadonly_rhel(setup):
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    patches = master['fixture'].salt(minion['id'],
        'cmd.run "yum info-sec | grep \'Update ID\' | cut -d\' \' -f6"'
        )[minion['id']].encode('utf-8').split(os.linesep)
    patches = {"patches": filter(lambda x: "RHBA" in x, patches)[:2]}
    list_pkgs_pre = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    resp = master['fixture'].salt(minion['id'], 'state.apply patches-downloaded pillar=\'{0}\''.format(patches))
    list_pkgs_post = master['fixture'].salt(minion['id'], 'pkg.list_pkgs')
    assert resp[minion['id']]['pkg_|-test-patches-downloaded_|-test-patches-downloaded_|-installed']['result'] is True
    assert list_pkgs_pre == list_pkgs_post
