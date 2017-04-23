import pytest
from functools import partial


pytestmark = pytest.mark.usefixtures("master", "minion")


@pytest.fixture()
def test_repo(request, minion):
    repo_name = 'Repo-With-GPGkey'
    repo_path = '/tmp/test_repo/'

    with open('./tests/test_repo.tar.gz', 'rb') as f:
        minion['container']['config']['docker_client'].put_archive(
            minion['container']['config']['name'], '/tmp', f.read())

    request.addfinalizer(partial(minion.salt_call, 'pkg.del_repo', repo_name))
    return repo_name, repo_path


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


def test_pkgrepo_managed_change_base_url(minion, test_repo):
    name, path = test_repo
    new_baseurl = 'file:/{0}-changed'.format(path)
    # add the repository
    minion.salt_call(
        'pkg.mod_repo',
        'repo={0}'.format(name),
        'name={0}'.format(name),
        'baseurl=file://{0}'.format(path),
        'enabled=True',
        'cache=False',  # TODO: test with True
        'gpgcheck=False',
        'priority=2',  # TODO: test priority 1
        'autorefresh=True'
    )
    # modify the repository
    output = minion.salt_call(
        'pkg.mod_repo',
        name,
        'baseurl={0}'.format(new_baseurl),
        'enabled=False'
    )
    assert output == {
        u'alias': name,
        u'type': None,
        u'autorefresh': False,
        u'enabled': False,
        u'gpgcheck': False,
        u'keeppackages': False,
        u'priority': '2',
        u'baseurl': new_baseurl
    }
