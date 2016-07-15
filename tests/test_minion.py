import re
import pytest
from functools import partial
from utils import retry


pytestmark = pytest.mark.usefixtures("master", "minion", "minion_key_accepted")


def post_12_required(info):
    if info['VERSION'] < 12:
        pytest.skip("incompatible with this version")


def pre_12_required(info):
    if info['VERSION'] >= 12:
        pytest.skip("incompatible with this version")


def minor_0_required(info):
    if info['PATCHLEVEL'] != 0:
        pytest.skip("incompatible with this minor version")


def minor_non_0_required(info):
    if info['PATCHLEVEL'] == 0:
        pytest.skip("incompatible with this minor version")


def test_ping_minion(master, minion):

    def ping():
        return master.salt(minion['id'], "test.ping")[minion['id']]

    assert retry(ping)


def test_pkg_list(minion):
    assert minion.salt_call("pkg.list_pkgs")


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_owner(minion):
    assert minion.salt_call('pkg.owner', '/etc/zypp') == 'libzypp'


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_list_products_post_12(minion):
    post_12_required(minion['container'].get_suse_release())
    [output] = minion.salt_call('pkg.list_products')
    assert output['name'] == 'SLES'
    assert output['release'] == '0'


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_list_products_pre_12(minion):
    pre_12_required(minion['container'].get_suse_release())
    [output] = minion.salt_call('pkg.list_products')
    assert output['name'] == 'SUSE_SLES'


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_list_products_with_minor_0(minion):
    minor_0_required(minion['container'].get_suse_release())
    info = minion['container'].get_suse_release()
    [output] = minion.salt_call('pkg.list_products')
    assert output['version'] == unicode(info['VERSION'])


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_list_products_with_minor_non_0(minion):
    minor_non_0_required(minion['container'].get_suse_release())
    info = minion['container'].get_suse_release()
    [output] = minion.salt_call('pkg.list_products')
    assert output['version'] == "{VERSION}.{PATCHLEVEL}".format(**info)


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_list_products_with_OEM_release(request, minion):
    suse_register = '/var/lib/suseRegister'
    filepath = suse_register + '/OEM/sles'
    minion['container'].run('mkdir -p {0}'.format(suse_register + '/OEM'))
    with open('tests/oem_sles.tar', 'rb') as f:
        minion['container']['config']['docker_client'].put_archive(
            minion['container']['config']['name'],
            suse_register + '/OEM',
            f.read()
        )
    request.addfinalizer(
        lambda: minion['container'].run('rm -rf {0}'.format(suse_register)))

    minion['container'].run("echo 'OEM' > {0}".format(filepath))
    [output] = minion.salt_call('pkg.list_products')
    assert output['productline'] == 'sles'
    assert output['release'] == 'OEM'


@pytest.mark.tags_xfail('rhel', 'sles11sp3', 'sles11sp4')
def test_zypper_pkg_modrepo_create(request, minion):
    repo_name = 'repotest'
    request.addfinalizer(
        partial(minion['container'].run, 'zypper rr {0}'.format(repo_name)))
    repo_path = '/tmp/' + repo_name
    minion['container'].run('mkdir {0}'.format(repo_path))
    output = minion.salt_call(
        'pkg.mod_repo', repo_name, "url=file:///{0}".format(repo_path))
    assert output == {
        u'alias': repo_name,
        u'type': None,
        u'autorefresh': False,
        u'enabled': True,
        u'baseurl': u'file:/%2Ftmp/repotest'
    }


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_modrepo_modify(request, minion):
    repo_name = 'repotest-1'
    request.addfinalizer(
        partial(minion['container'].run, 'zypper rr {0}'.format(repo_name)))
    repo_path = '/tmp/' + repo_name
    minion.salt_call(
        'pkg.mod_repo', repo_name, "url=file:///{0}".format(repo_path))
    output = minion.salt_call(
        'pkg.mod_repo', repo_name, 'refresh=True', 'enabled=False')
    assert output['enabled'] is False
    assert output['autorefresh'] is True


@pytest.mark.tags_xfail('rhel')
def test_zypper_refresh_repo_with_gpgkey(request, master, minion):
    repo_name = 'Repo-With-GPGkey'

    with open('./tests/test_repo.tar.gz', 'rb') as f:
        minion['container']['config']['docker_client'].put_archive(
            minion['container']['config']['name'], '/tmp', f.read())

    request.addfinalizer(
        partial(minion['container'].run, 'zypper rr {0}'.format(repo_name)))

    minion.salt_call(
        'pkg.mod_repo',
        repo_name,
        'name={0}'.format(repo_name),
        'disabled=False',
        'url=file:///tmp/test_repo/',
        'refresh=True',
        'gpgautoimport=True'
    )
    # do not use pkg.mod_repo next
    # assert `zypper refresh` doesn't ask for gpg confirmation anymore
    res = minion['container'].run('zypper refresh')
    assert "Repository '{0}' is up to date.".format(repo_name) in res


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_del_repo(minion):
    repo_name = 'repotest-2'
    repo_path = '/tmp/' + repo_name
    minion.salt_call(
        'pkg.mod_repo', repo_name, "url=file:///{0}".format(repo_path))
    res = minion.salt_call('pkg.del_repo', repo_name)
    assert res[repo_name] is True


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_refresh_db(minion):
    res = minion.salt_call('pkg.refresh_db')
    assert res['testpackages'] is True


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_list_patterns(minion):
    res = minion.salt_call('pkg.list_patterns')
    assert res['Minimal']['installed'] is False


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_search(minion):
    res = minion.salt_call('pkg.search', 'test-package')
    assert re.match(
        "Test package for Salt's (pkg.info_installed\/)*pkg.latest",
        res['test-package-zypper']['summary'])


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_download(minion):
    post_12_required(minion['container'].get_suse_release())
    res = minion.salt_call('pkg.download', 'test-package')
    assert res['test-package']['repository-alias'] == 'salt'


@pytest.mark.tags_xfail('rhel')
def test_zypper_pkg_remove(request, minion):
    res = minion.salt_call('pkg.remove', 'test-package')
    request.addfinalizer(
        partial(minion['container'].run, 'zypper in test-package'))
    assert res['test-package']['new'] == ''
