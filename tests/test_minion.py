import re
import pytest
from functools import partial
from utils import retry


pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.fixture()
def test_repo(request, minion):
    repo_name = 'Repo-With-GPGkey'
    repo_path = '/tmp/test_repo/'

    with open('./tests/test_repo.tar.gz', 'rb') as f:
        minion['container']['config']['client'].put_archive(
            minion['container']['config']['name'], '/tmp', f.read())

    request.addfinalizer(partial(minion.salt_call, 'pkg.del_repo', repo_name))
    return repo_name, repo_path


def test_ping_minion(master, minion):

    def ping():
        return master.salt(minion['id'], "test.ping")[minion['id']]

    assert retry(ping)


def test_pkg_list(minion):
    assert minion.salt_call("pkg.list_pkgs")


@pytest.mark.skiptags('rhel')
def test_pkg_owner(minion):
    assert minion.salt_call('pkg.owner', '/etc/zypp') == 'libzypp'


@pytest.mark.xfailtags('rhel', 'sles11sp3', 'sles11sp4')
def test_pkg_modrepo_create(request, minion, test_repo):
    name, path = test_repo
    output = minion.salt_call(
        'pkg.mod_repo',
        'repo={0}'.format(name),
        'name={0}'.format(name),
        'baseurl=file://{0}'.format(path)
    )
    assert output == {
        u'alias': name,
        u'type': None,
        u'autorefresh': False,
        u'enabled': True,
        u'baseurl': u'file:{0}'.format(path)
    }


@pytest.mark.xfailtags('rhel', 'sles11sp3', 'sles11sp4')
def test_pkg_modrepo_modify(request, minion, test_repo):
    name, path = test_repo
    # add the repository
    minion.salt_call(
        'pkg.mod_repo',
        'repo={0}'.format(name),
        'name={0}'.format(name),
        'baseurl=file://{0}'.format(path)
    )
    # modify the repository
    output = minion.salt_call(
        'pkg.mod_repo',
        name,
        'refresh=True',
        'enabled=False'
    )
    assert output == {
        u'alias': name,
        u'type': None,
        u'autorefresh': True,
        u'enabled': False,
        u'baseurl': u'file:{0}'.format(path)
    }


@pytest.mark.tags('sles')
def test_zypper_refresh_repo_with_gpgkey(request, master, minion, test_repo):
    name, path = test_repo
    minion.salt_call(
        'pkg.mod_repo',
        'repo={0}'.format(name),
        'name={0}'.format(name),
        'disabled=False',
        'baseurl=file://{0}'.format(path),
        'refresh=True',
        'gpgautoimport=True'
    )
    # do not use pkg.mod_repo next
    # assert `zypper refresh` doesn't ask for gpg confirmation anymore
    res = minion['container'].run('zypper refresh')
    assert "Repository '{0}' is up to date.".format(name) in res


@pytest.mark.xfailtags('rhel')
def test_pkg_del_repo(minion):
    repo_name = 'repotest-2'
    repo_path = '/tmp/' + repo_name
    minion.salt_call(
        'pkg.mod_repo',
        'repo={0}'.format(repo_name),
        'name={0}'.format(repo_name),
        "baseurl=file:///{0}".format(repo_path))
    res = minion.salt_call('pkg.del_repo', repo_name)
    assert res[repo_name] is True


@pytest.mark.xfailtags('rhel')
def test_pkg_refresh_db(minion):
    res = minion.salt_call('pkg.refresh_db')
    assert res['testpackages'] is True


@pytest.mark.skiptags('leap')
@pytest.mark.xfailtags('rhel')
def test_pkg_list_patterns(minion):
    res = minion.salt_call('pkg.list_patterns')
    assert res['base']['installed'] is False


@pytest.mark.xfailtags('rhel')
def test_pkg_search(minion):
    res = minion.salt_call('pkg.search', 'test-package')
    assert re.match(
        "Test package for Salt's (pkg.info_installed\/)*pkg.latest",
        res['test-package-zypper']['summary'])


@pytest.mark.xfailtags('rhel')
@pytest.mark.tags('sles12', 'sles12sp1')
def test_pkg_download(minion):
    res = minion.salt_call('pkg.download', 'test-package')
    assert 'repository-alias' in res['test-package']
    assert res['test-package']['repository-alias'] in ['salt', 'testpackages']


def test_pkg_remove(request, minion):
    minion.salt_call('pkg.install', 'test-package')
    res = minion.salt_call('pkg.remove', 'test-package')
    assert res['test-package']['new'] == ''
