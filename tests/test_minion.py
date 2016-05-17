import shlex
import pytest
from assertions import assert_minion_key_state
from jinja2 import Environment, PackageLoader
from config import SALT_CALL
from utils import check_output


pytestmark = pytest.mark.usefixtures(
    "top", "master", "minion", "wait_minion_key_cached")


@pytest.fixture(scope="module")
def add_repo_sls(file_roots, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('systemsmanagement_saltstack.sls')
    env.update({
        'REPO_URL': 'http://download.opensuse.org/repositories/systemsmanagement:/saltstack/SLE_12_SP1/',
        'GPGKEY_URL': 'http://download.opensuse.org/repositories/systemsmanagement:/saltstack/SLE_12_SP1//repodata/repomd.xml.key'
    })
    content = template.render(**env)
    with (file_roots / 'systemsmanagement_saltstack.sls').open('wb') as f:
        f.write(content)


@pytest.fixture(scope="module")
def top(file_roots, add_repo_sls, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('top_add_repo.sls')
    content = template.render(**env)
    with (file_roots / 'top.sls').open('wb') as f:
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


def test_zypper_refresh_repo_with_gpgkey(env, local_client, minion_highstate):
    res = local_client.cmd(env['HOSTNAME'], 'cmd.run', ['zypper ref'])
    assert 'systemsmanagement_saltstack' in res[env['HOSTNAME']]
