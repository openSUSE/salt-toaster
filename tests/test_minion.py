import shlex
import pytest
import salt.config
import salt.client
from functools import partial
from assertions import assert_minion_key_state
from jinja2 import Environment, PackageLoader
from config import SALT_CALL
from utils import check_output


pytestmark = pytest.mark.usefixtures(
    "master", "minion", "wait_minion_key_cached")


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


def test_minion_key_cached(env):
    assert_minion_key_state(env, "unaccepted")


def test_minion_key_accepted(env, accept_key):
    assert_minion_key_state(env, "accepted")


def test_ping_minion(env, minion_ready):
    cmd = shlex.split(SALT_CALL.format(**env))
    cmd.append("test.ping")
    output = check_output(cmd, env)
    assert [env['HOSTNAME'], 'True'] == [it.strip() for it in output.split(':')]


def remove_repo(local_client, identifier, env):
    local_client.cmd(
        env['HOSTNAME'], 'cmd.run', ['zypper rr "{0}"'.format(identifier)])


@pytest.mark.xfail
def test_zypper_refresh_repo_with_gpgkey(request, env, minion_config, local_client, minion_ready):
    repo_name = 'Repo-With-GPGkey'
    request.addfinalizer(partial(remove_repo, local_client, repo_name, env))
    opts = salt.config.minion_config(minion_config.strpath)
    caller = salt.client.Caller(mopts=opts)
    caller.cmd(
        'pkg.mod_repo',
        repo_name,
        disabled=False,
        url="http://download.opensuse.org/repositories/devel:/libraries:/c_c++/SLE_12/",
        refresh=True,
        gpgautoimport=True
    )
    res = local_client.cmd(env['HOSTNAME'], 'cmd.run', ['zypper refresh'])
    assert "Repository '{0}' is up to date.".format(repo_name) in res[env['HOSTNAME']]
