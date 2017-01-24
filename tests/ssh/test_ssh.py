import pytest
import hashlib
import time

from saltcontainers.factories import ContainerFactory

from tests.common import GRAINS_EXPECTATIONS
from conftest import USER, PASSWORD
import json

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
    Test pkg.info_instaled on RHEL series
    '''
    assert master.salt_ssh("pkg.info_installed python").get('python', {}).get('install_date')


def test_ssh_pkg_install(master):
    '''
    Test pkg.install
    '''
    master.salt_ssh("cmd.run 'rpm -e test-package'")
    out = master.salt_ssh("pkg.install test-package")
    assert out.get('test-package', {}).get('new')
    assert not out.get('test-package', {}).get('old')


@pytest.mark.tags('rhel')
def test_ssh_pkg_remove_rhel(master):
    '''
    Test pkg.remove on RHEL
    '''
    master.salt_ssh("cmd.run 'yum install test-package -y'")
    out = master.salt_ssh("pkg.remove test-package")
    assert out.get('test-package', {}).get('old')
    assert not out.get('test-package', {}).get('new')


@pytest.mark.tags('sles', 'leap')
def test_ssh_pkg_remove_sles(master):
    '''
    Test pkg.remove on SLES
    '''
    master.salt_ssh("cmd.run 'zypper --non-interactive in test-package'")
    out = master.salt_ssh("pkg.remove test-package")
    assert out.get('test-package', {}).get('old')
    assert not out.get('test-package', {}).get('new')


def test_master_tops_support(master):
    '''
    Test https://github.com/saltstack/salt/pull/38021
    '''
    assert 'custom_top' in master.salt_ssh("state.show_top").get('base')


@pytest.mark.tags('rhel')
def test_ssh_port_forwarding_rhel(master):
    '''
    Platform: RHEL
    Test SSH port forwarding feature.
    PR: https://github.com/saltstack/salt/pull/38021
    '''
    ssh_port_forwarding(master, 'rhel')


@pytest.mark.tags('sles', 'leap')
def test_ssh_port_forwarding_sles(master):
    '''
    Platform: SLES
    Test SSH port forwarding feature.
    PR: https://github.com/saltstack/salt/pull/38021
    '''
    ssh_port_forwarding(master, 'sles')
    

def ssh_port_forwarding(master, platform):
    '''
    Test SSH port forwarding feature.
    '''
    msg = hashlib.sha256(str(time.time())).hexdigest()
    nc = "/salt-toaster/tests/scripts/netsend.sh"
    of = "/tmp/socket-8888.txt"
    loc_port = 8888
    rem_port = 9999

    if platform == 'sles':
        netcat_install = "zypper --non-interactive in netcat-openbsd"
    else:
        netcat_install = 'yum install nc -y'

    master.salt_ssh("cmd.run '{}'".format(netcat_install))
    master['container'].run("/salt-toaster/tests/scripts/socket_server.py {lp} {of}".format(lp=loc_port, of=of))
    master.salt_ssh("--remote-port-forwards={rp}:127.0.0.1:{lp} cmd.run '{nc} {msg} {rp}'".format(
        nc=nc, msg=msg, lp=loc_port, rp=rem_port)
    )

    assert master['container'].run("cat {}".format(of)).strip() == msg


@pytest.fixture(scope="module")
def sshdcontainer(request, salt_root, docker_client):
    obj = ContainerFactory(
        config__docker_client=docker_client,
        config__image=request.config.getini('MINION_IMAGE') or request.config.getini('IMAGE'),
        config__salt_config=None)

    obj.run('ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -q -N ""')
    obj.run('ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -q -N ""')
    obj.run('ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -q -N ""')
    obj.run('./tests/scripts/chpasswd.sh {}:{}'.format(USER, PASSWORD))
    obj.run('/usr/sbin/sshd -p 2222')
    obj.run('zypper --non-interactive rm salt')  # Remove salt from the image!!

    request.addfinalizer(obj.remove)
    return obj


def test_ssh_option(master, sshdcontainer):
    '''
    Test test.ping working.
    '''

    master['container'].run("zypper --non-interactive in netcat-openbsd")
    SSH = (
        "salt-ssh -l quiet -i --out json --key-deploy --passwd admin123 "
        "--ssh-option='ProxyCommand=\"nc {0} 2222\"' target network.ip_addrs"
    ).format(sshdcontainer['ip'])
    return json.loads(master['container'].run(SSH)).get('target') == sshdcontainer['ip']