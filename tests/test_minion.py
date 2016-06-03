import os
import shutil
import shlex
import pytest
from functools import partial
from assertions import assert_minion_key_state
from jinja2 import Environment, PackageLoader
from config import SALT_CALL
from utils import check_output, get_suse_release


pytestmark = pytest.mark.usefixtures("master", "minion")


def post_12_required():
    if get_suse_release()['VERSION'] < 12:
        pytest.skip("incompatible with this version")


def pre_12_required():
    if get_suse_release()['VERSION'] >= 12:
        pytest.skip("incompatible with this version")


def minor_0_required():
    if get_suse_release()['PATCHLEVEL'] != 0:
        pytest.skip("incompatible with this minor version")


def minor_non_0_required():
    if get_suse_release()['PATCHLEVEL'] == 0:
        pytest.skip("incompatible with this minor version")


@pytest.fixture(scope="module")
def add_repo_sls(file_roots, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('systemsmanagement_saltstack.sls')
    env.update({
        'REPO_URL': 'http://download.opensuse.org/repositories/devel:/libraries:/c_c++/SLE_12/',
        'GPGKEY_URL': 'http://download.opensuse.org/repositories/devel:/libraries:/c_c++/SLE_12//repodata/repomd.xml.key'
    })
    content = template.render(**env)
    with (file_roots / 'systemsmanagement_saltstack.sls').open('wb') as f:
        f.write(content)


def test_minion_key_cached(env, wait_minion_key_cached):
    assert_minion_key_state(env, "unaccepted")


def test_minion_key_accepted(env, accept_minion_key):
    assert_minion_key_state(env, "accepted")


def test_ping_minion(env, minion_ready):
    cmd = shlex.split(SALT_CALL.format(**env))
    cmd.append("test.ping")
    output = check_output(cmd, env)
    assert [env['HOSTNAME'], 'True'] == [it.strip() for it in output.split(':')]


def remove_repo(caller_client, identifier, env):
    caller_client.cmd('pkg.del_repo', identifier)


def test_pkg_list(caller_client, minion_ready):
    assert caller_client.cmd('pkg.list_pkgs')


def test_zypper_pkg_owner(caller_client, minion_ready):
    assert caller_client.cmd('pkg.owner', '/etc/zypp') == 'libzypp'


def test_zypper_pkg_list_products_post_12(caller_client, minion_ready):
    post_12_required()
    [output] = caller_client.cmd('pkg.list_products')
    assert output['name'] == 'SLES'
    assert output['release'] == '0'


def test_zypper_pkg_list_products_pre_12(caller_client, minion_ready):
    pre_12_required()
    [output] = caller_client.cmd('pkg.list_products')
    assert output['name'] == 'SUSE_SLES'


def test_zypper_pkg_list_products_with_minor_0(caller_client, minion_ready, suse_release):
    minor_0_required()
    [output] = caller_client.cmd('pkg.list_products')
    assert output['version'] == unicode(suse_release['VERSION'])


def test_zypper_pkg_list_products_with_minor_non_0(caller_client, minion_ready, suse_release):
    minor_non_0_required()
    [output] = caller_client.cmd('pkg.list_products')
    assert output['version'] == "{VERSION}.{PATCHLEVEL}".format(**suse_release)


def test_zypper_pkg_list_products_with_OEM_release(request, caller_client, minion_ready, suse_release):
    suse_register = '/var/lib/suseRegister'
    filepath = suse_register + '/OEM/sles'
    os.makedirs(suse_register + '/OEM')
    request.addfinalizer(lambda: shutil.rmtree(suse_register))
    with open(filepath, 'w+b') as f:
        f.write('OEM')
    [output] = caller_client.cmd('pkg.list_products')
    assert output['productline'] == 'sles'
    assert output['release'] == 'OEM'


def test_zypper_pkg_modrepo_create(request, env, caller_client, minion_ready, tmpdir_factory):
    repo_name = 'repotest'
    repo_dir = tmpdir_factory.mktemp(repo_name)
    caller_client.cmd(
        'pkg.mod_repo', repo_name, url="file:///{0}".format(repo_dir.strpath))
    request.addfinalizer(partial(remove_repo, caller_client, repo_name, env))


def test_zypper_pkg_modrepo_modify(request, env, caller_client, minion_ready, tmpdir_factory):
    repo_name = 'repotest-1'
    request.addfinalizer(partial(remove_repo, caller_client, repo_name, env))
    repo_dir = tmpdir_factory.mktemp(repo_name)
    caller_client.cmd(
        'pkg.mod_repo', repo_name, url="file:///{0}".format(repo_dir.strpath))
    output = caller_client.cmd(
        'pkg.mod_repo', repo_name, refresh=True, enabled=False, output="json")
    assert output['enabled'] is False
    assert output['autorefresh'] is True


def test_zypper_refresh_repo_with_gpgkey(request, env, local_client, caller_client, minion_ready):
    repo_name = 'Repo-With-GPGkey'
    request.addfinalizer(partial(remove_repo, caller_client, repo_name, env))
    caller_client.cmd(
        'pkg.mod_repo',
        repo_name,
        disabled=False,
        url="http://download.opensuse.org/repositories/devel:/libraries:/c_c++/SLE_12/",
        refresh=True,
        gpgautoimport=True
    )
    # do not use caller_client next
    # assert `zypper refresh` doesn't ask for gpg confirmation anymore
    res = local_client.cmd(env['HOSTNAME'], 'cmd.run', ['zypper refresh'])
    assert "Repository '{0}' is up to date.".format(repo_name) in res[env['HOSTNAME']]


def test_zypper_pkg_del_repo(request, env, caller_client, minion_ready, tmpdir_factory):
    repo_name = 'repotest-2'
    repo_dir = tmpdir_factory.mktemp(repo_name)
    caller_client.cmd(
        'pkg.mod_repo', repo_name, url="file:///{0}".format(repo_dir.strpath))
    res = caller_client.cmd('pkg.del_repo', repo_name)
    assert res[repo_name] is True


def test_zypper_pkg_refresh_db(request, env, caller_client, minion_ready):
    res = caller_client.cmd('pkg.refresh_db')
    assert res['testpackages'] is True


def test_zypper_pkg_list_patterns(request, env, caller_client, minion_ready):
    res = caller_client.cmd('pkg.list_patterns')
    assert res['Minimal']['installed'] is False


def test_zypper_pkg_search(request, env, caller_client, minion_ready):
    res = caller_client.cmd('pkg.search', 'test-package')
    assert res['test-package-zypper']['summary'] == u"Test package for Salt's pkg.latest"


def test_zypper_pkg_download(request, env, caller_client, minion_ready):
    post_12_required()
    res = caller_client.cmd('pkg.download', 'test-package')
    assert res['test-package']['repository-alias'] == 'salt_testing'


def install_package(caller_client, package):
    caller_client.cmd('pkg.install', 'test-package')


def test_zypper_pkg_remove(request, env, caller_client, minion_ready):
    res = caller_client.cmd('pkg.remove', 'test-package')
    request.addfinalizer(partial(install_package, caller_client, 'test-package'))
    assert res['test-package']['new'] == ''
