import re
import pytest
from utils import retry
from functools import partial

pytestmark = pytest.mark.usefixtures("master", "minion")

@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                'config': {
                    'container__config__salt_config__sls': [
                        'tests/sls/rsync.sls',
                        'tests/sls/archextract.sls',
                    ]
                },
                'minions': [
                    {
                        "config": {
                            "container__config__image": (
                                request.config.getini('MINION_IMAGE') or
                                request.config.getini('IMAGE')
                            )
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture()
def master(setup):
    config, initconfig = setup
    return config['masters'][0]['fixture']


@pytest.fixture()
def minion(setup):
    config, initconfig = setup
    master = config['masters'][0]
    return master['minions'][0]['fixture']


@pytest.mark.tags('sles')
def test_zypp_gpg_pkg(master, minion):
    '''
    Fake packages gpg-pubkey* should be filtered out by zypper.
    '''
    resp = master.salt(minion['id'], "pkg.info_installed")[minion['id']]
    assert not bool([pk for pk in resp.keys() if 'gpg-pubkey' in pk])


def test_rsync_port(master, minion):
    '''
    Test rsync port from 2016.3.
    '''
    resp = master.salt(minion['id'], "state.apply rsync")[minion['id']]
    assert resp['pkg_|-rsyncpackage_|-rsync_|-installed']['result']
    assert resp['rsync_|-/tmp_|-/tmp_|-synchronized']['result']


def _archextract(master, minion):
    try:
        resp = master.salt(minion['id'], "state.apply archextract")[minion['id']]
        return resp['archive_|-extract-zip-archive_|-/tmp/_|-extracted']['result']
    except TypeError:
        return False


def test_archive_extracted(master, minion):
    '''
    Test if the archive.extracted overwrites the destination.
    '''
    assert retry(partial(_archextract, master, minion))


@pytest.mark.tags('rhel')
def test_yum_plugin_installed(master, minion):
    path = '/etc/yum/pluginconf.d/yumnotify.conf'
    out = master.salt(minion['id'], 'cmd.run "file {}"'.format(path))[minion['id']]
    assert out == '{}: ASCII text'.format(path)

    path = '/usr/share/yum-plugins/yumnotify.py'
    out = master.salt(minion['id'], 'cmd.run "file {}"'.format(path))[minion['id']]
    assert '{}: Python script'.format(path) in out
    assert 'text executable' in out


@pytest.mark.xfailtags('rhel', 'sles', 'leap')
@pytest.mark.tags('sles', 'leap')
def test_change_tz(master, minion):
    assert master.salt(minion['id'], "timezone.set_zone UTC")[minion['id']]
    assert master.salt(minion['id'], "timezone.get_zone")[minion['id']] == 'UTC'
