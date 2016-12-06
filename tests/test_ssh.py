import pytest
import json
from functools import partial
from common import GRAINS_EXPECTATIONS
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


def pytest_generate_tests(metafunc):
    '''
    Call listed functions with the grain params.
    '''

    functions = [
        'test_ssh_grain_os',
        'test_ssh_grain_oscodename',
        'test_ssh_grain_os_family',
        'test_ssh_grain_osfullname',
        'test_ssh_grain_osrelease',
        'test_ssh_grain_osrelease_info',
    ]

    expectations = GRAINS_EXPECTATIONS

    # TODO: Replace this construction with just reading a current version
    version = set(set(metafunc.config.getini('TAGS'))).intersection(set(expectations)).pop()
    if metafunc.function.func_name in functions and version:
        metafunc.parametrize('expected', [expectations[version]], ids=lambda it: version)


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


def test_ssh_grain_os(master, expected):
    grain = 'os'
    assert master.salt_ssh("grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_oscodename(master, expected):
    grain = 'oscodename'
    assert master.salt_ssh("grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_os_family(master, expected):
    grain = 'os_family'
    assert master.salt_ssh("grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_osfullname(master, expected):
    grain = 'osfullname'
    assert master.salt_ssh("grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_osrelease(master, expected):
    grain = 'osrelease'
    assert master.salt_ssh("grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_osrelease_info(master, expected):
    grain = 'osrelease_info'
    assert master.salt_ssh("grains.get {}".format(grain)) == expected[grain]


def test_ssh_ping(master):
    '''
    Test test.ping working.
    '''
    assert master.salt_ssh("test.ping")  # Returns True


def test_ssh_cmdrun(master):
    '''
    Test grains over Salt SSH
    '''
    assert master.salt_ssh("cmd.run 'uname'") == 'Linux'


def test_ssh_pkg_info(master):
    '''
    Test pkg.info
    '''
    assert master.salt_ssh("pkg.info python").get('python', {}).get('installed')

def test_ssh_pkg_install(master):
    '''
    Test pkg.install
    '''
    master.salt_ssh("cmd.run 'zypper --non-interactive rm test-package'")
    out = master.salt_ssh("pkg.install test-package")
    assert bool(out.get('test-package', {}).get('new'))
    assert not bool(out.get('test-package', {}).get('old'))


def test_ssh_pkg_remove(master):
    '''
    Test pkg.remove
    '''
    master.salt_ssh("cmd.run 'zypper --non-interactive in test-package'")
    out = master.salt_ssh("pkg.remove test-package")
    assert bool(out.get('test-package', {}).get('old'))
    assert not bool(out.get('test-package', {}).get('new'))
