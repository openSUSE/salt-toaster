import pytest
import json
from saltcontainers.factories import ContainerFactory

USER = "root"
PASSWORD = "admin123"
SSH = "salt-ssh -i --out json --key-deploy --passwd {0} target {1}".format(PASSWORD, '{0}')

@pytest.fixture(scope='module')
def module_config(request, container):
    return {
        "masters": [
            {
                "config": {
                    "container__config__salt_config__extra_configs": {
                        "thin_extra_mods": {
                            "thin_extra_mods": "msgpack"
                        }
                    },
                    "container__config__salt_config__apply_states": {
                        "top": "tests/sls/ssh/top.sls",
                        "ssh": "tests/sls/ssh/ssh.sls"
                    },
                    "container__config__salt_config__roster": {
                        "target": {
                            "host": container["ip"],
                            "user": USER,
                            "password": PASSWORD
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def container(request, salt_root, docker_client):
    obj = ContainerFactory(
        config__docker_client=docker_client,
        config__image=request.config.getini('IMAGE'),
        config__salt_config=None)

    obj.run('ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -q -N ""')
    obj.run('ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -q -N ""')
    obj.run('ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -q -N ""')
    obj.run('./tests/scripts/chpasswd.sh {}:{}'.format(USER, PASSWORD))
    obj.run('/usr/sbin/sshd')
    obj.run('zypper --non-interactive rm salt')  # Remove salt from the image!!

    request.addfinalizer(obj.remove)
    return obj


def _cmd(setup, cmd):
    '''
    Get container from the setup and run given command on it.

    :param setup: Setup
    :param cmd: An SSH command
    '''
    config, initconfig = setup
    master = config['masters'][0]['fixture']
    return json.loads(master['container'].run(SSH.format(cmd)))


def test_ssh_ping(setup):
    '''
    Test test.ping working.
    '''
    assert _cmd(setup, "test.ping")['target']  # Returns True


def test_ssh_cmdrun(setup):
    '''
    Test grains over Salt SSH
    '''
    assert _cmd(setup, "cmd.run 'uname'")['target'] == 'Linux'


def test_ssh_pkg_info(setup):
    '''
    Test pkg.info
    '''
    assert _cmd(setup, "pkg.info python")['target'].get('python', {}).get('installed')

def test_ssh_pkg_install(setup):
    '''
    Test pkg.install
    '''
    _cmd(setup, "cmd.run 'zypper --non-interactive rm test-package'")
    out = _cmd(setup, "pkg.install test-package")
    assert bool(out['target'].get('test-package', {}).get('new'))
    assert not bool(out['target'].get('test-package', {}).get('old'))


def test_ssh_pkg_remove(setup):
    '''
    Test pkg.remove
    '''
    _cmd(setup, "cmd.run 'zypper --non-interactive in test-package'")
    out = _cmd(setup, "pkg.remove test-package")
    assert bool(out['target'].get('test-package', {}).get('old'))
    assert not bool(out['target'].get('test-package', {}).get('new'))
