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


def test_ssh_ping(setup, container):
    '''
    Test test.ping working.
    '''
    assert _cmd(setup, "test.ping")['target']  # Returns True


def test_ssh_cmdrun(setup):
    '''
    Test grains over Salt SSH
    '''
    assert _cmd(setup, "cmd.run 'uname'")['target'] == 'Linux'
