import pytest
import json
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
                        }
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


@pytest.fixture()
def master(setup):
    config, initconfig = setup
    master = config['masters'][0]['fixture']
    def _cmd(master, cmd):
        SSH = "salt-ssh -i --out json --key-deploy --passwd {0} {1} {{0}}".format(
            PASSWORD, TARGET_ID)
        return json.loads(
            master['container'].run(SSH.format(cmd))).get(TARGET_ID)
    master.salt_ssh = partial(_cmd, master)
    return master


@pytest.mark.tags('sles')
def test_pkg_owner(setup):
    '''
    Test pkg.owner
    '''
    #assert master.salt_ssh("pkg.owner /etc/zypp") == 'libzypp'


@pytest.mark.tags('sles')
def test_pkg_list_products(master):
    '''
    List test products
    '''
    products = master.salt_ssh("pkg.list_products")
    for prod in products:
        if prod['productline'] == 'sles':
            assert prod['productline'] == 'sles'
            assert prod['name'] == 'SLES'
            assert prod['vendor'] == 'SUSE'
            assert prod['isbase']
            assert prod['installed']
            break
        else:
            raise Exception("Product not found")

def test_pkg_search(master):
    assert 'test-package-zypper' in master.salt_ssh("pkg.search test-package")


def test_pkg_repo(master):
    assert master.salt_ssh('pkg.list_repos')['testpackages']['enabled']

def test_pkg_mod_repo(master):
    assert not master.salt_ssh('pkg.mod_repo testpackages enabled=false')['enabled']
    assert master.salt_ssh('pkg.mod_repo testpackages enabled=true')['enabled']


def test_pkg_del_repo(master):
    msg = "Repository 'testpackages' has been removed."
    out = master.salt_ssh('pkg.del_repo testpackages')
    assert out['message'] == msg
    assert out['testpackages']

