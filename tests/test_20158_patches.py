import re
import pytest
import pdb

pytestmark = pytest.mark.usefixtures("master", "minion")

@pytest.fixture(scope='module')
def module_config(request):
    return {
        'masters': [
            {
                'config': {
                    'container__config__salt_config__sls': {
                        'rsync': 'tests/sls/rsync.sls',
                        'archextract': 'tests/sls/archextract.sls',
                    }
                },
                'minions': [{'config': {}}, {'config': {}}]
            }
        ]
    }


def _minion(setup, cmd):
    '''
    Call salt on current minion
    '''
    config, initconfig = setup
    master = config['masters'][0]
    minion = master['minions'][0]
    return master['fixture'].salt(minion['id'], cmd)[minion['id']]


@pytest.mark.tags('sles')
def test_zypp_gpg_pkg(setup):
    '''
    Fake packages gpg-pubkey* should be filtered out by zypper.
    '''
    assert not bool([pk for pk in _minion(setup, "pkg.info_installed").keys() if 'gpg-pubkey' in pk])


def test_rsync_port(setup):
    '''
    Test rsync port from 2016.3.
    '''
    resp = _minion(setup, "state.apply rsync")
    assert resp['pkg_|-rsyncpackage_|-rsync_|-installed']['result']
    assert resp['rsync_|-/tmp_|-/tmp_|-synchronized']['result']


def test_archive_extracted(setup):
    '''
    Test if the archive.extracted overwrites the destination.
    '''
    assert _minion(setup, "state.apply archextract")\
        ['archive_|-extract-zip-archive_|-/tmp/_|-extracted']['result']
