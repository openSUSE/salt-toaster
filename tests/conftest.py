import os
import shlex
import pytest
import subprocess
from jinja2 import Environment, PackageLoader
from utils import block_until_log_shows_message
from config import (
    SALT_MASTER_START_CMD, SALT_MINION_START_CMD, SALT_KEY_CMD,
    SALT_PROXYMINION_START_CMD
)


@pytest.fixture(scope="session")
def salt_root(tmpdir_factory):
    return tmpdir_factory.mktemp("salt")


@pytest.fixture(scope="session")
def user():
    return subprocess.check_output("whoami").strip()


@pytest.fixture(scope="session")
def master_config(salt_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('master')
    config = template.render(**env)
    with (salt_root / 'master').open('wb') as f:
        f.write(config)


@pytest.fixture(scope="session")
def minion_config(salt_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('minion')
    config = template.render(**env)
    with (salt_root / 'minion').open('wb') as f:
        f.write(config)


@pytest.fixture(scope="session")
def proxyminion_config(salt_root, env):
    jinja_env = Environment(loader=PackageLoader('tests', 'config'))
    template = jinja_env.get_template('proxy')
    config = template.render(**env)
    with (salt_root / 'proxy').open('wb') as f:
        f.write(config)


@pytest.fixture(scope="session")
def env(salt_root, user):
    env = dict(os.environ)
    env["USER"] = user
    env["SALT_ROOT"] = salt_root.strpath
    env["PROXY_ID"] = "proxy-minion"
    return env


def start_process(request, cmd, env):
    proc = subprocess.Popen(shlex.split(cmd.format(**env)), env=env)
    request.addfinalizer(proc.terminate)
    return proc


@pytest.fixture(scope="session")
def master(request, master_config, env):
    return start_process(request, SALT_MASTER_START_CMD, env)


@pytest.fixture(scope="session")
def minion(request, minion_config, env):
    return start_process(request, SALT_MINION_START_CMD, env)


@pytest.fixture(scope="session")
def proxyminion(request, proxyminion_config, env):
    return start_process(request, SALT_PROXYMINION_START_CMD, env)


@pytest.fixture(scope="session")
def wait_minion_key_cached(salt_root):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/minion'),
        message='Salt Master has cached the public key'
    )


@pytest.fixture(scope="session")
def wait_proxyminion_key_cached(salt_root):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/proxy'),
        message='Salt Master has cached the public key'
    )


@pytest.fixture(scope="session")
def accept_keys(env, salt_root):
    CMD = SALT_KEY_CMD + " -A --yes"
    cmd = shlex.split(CMD.format(**env))
    subprocess.check_output(cmd, env=env)


@pytest.fixture(scope="session")
def minion_ready(env, salt_root, accept_keys):
    block_until_log_shows_message(
        log_file=(salt_root / 'var/log/salt/minion'),
        message='Minion is ready to receive requests!'
    )
