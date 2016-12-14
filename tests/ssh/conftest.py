import json
import pytest
from functools import partial
from saltcontainers.factories import ContainerFactory


USER = "root"
PASSWORD = "admin123"
TARGET_ID = "target"

@pytest.fixture(scope='module')
def module_config(request, container):
    return {
        "masters": [
            {
                "config": {
                    "container__config__salt_config__extra_configs": {
                        "thin_extra_mods": {
                            "thin_extra_mods": "msgpack"
                        },
                        "custom_tops": {
                            "extension_modules": "/salt-toaster/tests/sls/ssh/xmod",
                            "master_tops": {
                                "toptest": True
                            },
                        },
                    },
                    "container__config__salt_config__apply_states": {
                        "top": "tests/sls/ssh/top.sls",
                        "ssh": "tests/sls/ssh/ssh.sls"
                    },
                    "container__config__salt_config__roster": {
                        TARGET_ID: {
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
        config__image=request.config.getini('MINION_IMAGE') or request.config.getini('IMAGE'),
        config__salt_config=None)

    obj.run('ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -q -N ""')
    obj.run('ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -q -N ""')
    obj.run('ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -q -N ""')
    obj.run('./tests/scripts/chpasswd.sh {}:{}'.format(USER, PASSWORD))
    obj.run('/usr/sbin/sshd')
    obj.run('zypper --non-interactive rm salt')  # Remove salt from the image!!

    request.addfinalizer(obj.remove)
    return obj


@pytest.fixture()
def master(setup):
    config, initconfig = setup
    master = config['masters'][0]['fixture']
    def _cmd(master, cmd):
        SSH = "salt-ssh -i --out json --key-deploy --passwd {0} {1} {{0}}".format(
            PASSWORD, TARGET_ID)
        out = master['container'].run(SSH.format(cmd))
        return json.loads(out).get(TARGET_ID)
    master.salt_ssh = partial(_cmd, master)
    return master
