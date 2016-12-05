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
    assert not bool([pk for pk in _minion(setup, "pkg.info_installed").keys() if 'gpg-pubkey' in pk])


def test_rsync_port(setup):
    resp = _minion(setup, "state.apply rsync")
    assert resp['pkg_|-rsyncpackage_|-rsync_|-installed']['result']
    assert resp['rsync_|-/tmp_|-/tmp_|-synchronized']['result']

