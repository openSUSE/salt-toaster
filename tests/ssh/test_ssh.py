import pytest
import hashlib
import time
import six

from faker import Faker
from saltcontainers.factories import ContainerFactory

from tests.common import GRAINS_EXPECTATIONS
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
    if metafunc.function.__name__ in functions and version:
        metafunc.parametrize('expected', [expectations[version]], ids=lambda it: version)
    if 'python' in metafunc.fixturenames:
        tags = set(metafunc.config.getini('TAGS'))
        if 'sles15' in tags or 'sles15sp1' in tags or 'opensuse' in tags:
            metafunc.parametrize("python", ["python3"])
        else:
            metafunc.parametrize("python", ["python"])


def test_ssh_grain_os(master, container, expected):
    grain = 'os'
    assert master.salt_ssh(
        container, "grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_oscodename(master, container, expected):
    grain = 'oscodename'
    assert master.salt_ssh(
        container, "grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_os_family(master, container, expected):
    grain = 'os_family'
    assert master.salt_ssh(
        container, "grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_osfullname(master, container, expected):
    grain = 'osfullname'
    assert master.salt_ssh(
        container, "grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_osrelease(master, container, expected):
    grain = 'osrelease'
    assert master.salt_ssh(
        container, "grains.get {}".format(grain)) == expected[grain]


def test_ssh_grain_osrelease_info(master, container, expected):
    grain = 'osrelease_info'
    assert master.salt_ssh(
        container, "grains.get {}".format(grain)) == expected[grain]


def test_ssh_ping(master, container):
    '''
    Test test.ping working.
    '''
    assert master.salt_ssh(container, "test.ping") is True


def test_ssh_cmdrun(master, container):
    '''
    Test grains over Salt SSH
    '''
    assert master.salt_ssh(container, "cmd.run 'uname'") == 'Linux'


@pytest.mark.skiptags('ubuntu')
def test_ssh_pkg_info(master, container):
    '''
    Test pkg.info_instaled on RHEL series
    '''
    assert master.salt_ssh(
        container,
        "pkg.info_installed test-package").get('test-package', {}).get('install_date')


def test_ssh_sysdoc(master, container):
    '''
    Test sys.doc remote execution.
    '''
    assert 'cmd.run' in master.salt_ssh(container, "sys.doc")


@pytest.mark.skiptags('ubuntu')
def test_ssh_pkg_install(master, container):
    '''
    Test pkg.install
    '''
    master.salt_ssh(container, "cmd.run 'rpm -e test-package'")
    out = master.salt_ssh(container, "pkg.install test-package")
    assert out.get('test-package', {}).get('new')
    assert not out.get('test-package', {}).get('old')


@pytest.mark.tags('rhel')
def test_ssh_pkg_remove_rhel(master, container):
    '''
    Test pkg.remove on RHEL
    '''
    master.salt_ssh(container, "cmd.run 'yum install test-package -y'")
    out = master.salt_ssh(container, "pkg.remove test-package")
    assert out.get('test-package', {}).get('old')
    assert not out.get('test-package', {}).get('new')


@pytest.mark.tags('sles', 'opensuse')
def test_ssh_pkg_remove_sles(master, container):
    '''
    Test pkg.remove on SLES
    '''
    master.salt_ssh(
        container, "cmd.run 'zypper --non-interactive in test-package'")
    out = master.salt_ssh(container, "pkg.remove test-package")
    assert out.get('test-package', {}).get('old')
    assert not out.get('test-package', {}).get('new')


def test_master_tops_support(master, container):
    '''
    Test https://github.com/saltstack/salt/pull/38021
    '''
    assert 'custom_top' in master.salt_ssh(container, "state.show_top").get('base')


@pytest.mark.skiptags('ubuntu')
def test_ssh_port_forwarding(master, container, python):
    '''
    Test SSH port forwarding feature.
    PR: https://github.com/saltstack/salt/pull/38021
    '''
    if six.PY3:
        msg = hashlib.sha256(str(time.time()).encode()).hexdigest()
    else:
        msg = hashlib.sha256(str(time.time())).hexdigest()
    nc = "/salt-toaster/tests/scripts/netsend.sh"
    of = "/tmp/socket-8888.txt"
    loc_port = 8888
    rem_port = 9999

    master['container'].run("{py} /salt-toaster/tests/scripts/socket_server.py {lp} {of}".format(py=python, lp=loc_port, of=of))
    params = "--remote-port-forwards={rp}:127.0.0.1:{lp} cmd.run '{nc} {msg} {rp}'".format(
        nc=nc, msg=msg, lp=loc_port, rp=rem_port)
    master.salt_ssh(container, params)

    assert str(master['container'].run("cat {}".format(of)).strip().decode()) == msg


@pytest.fixture(scope="module")
def sshdcontainer(request, salt_root):
    fake = Faker()
    obj = ContainerFactory(
        config__name='ssdcontainer_{0}_{1}_{2}'.format(fake.word(), fake.word(), os.environ.get('ST_JOB_ID', '')),  # pylint: disable=no-member
        config__image=request.config.getini('MINION_IMAGE') or request.config.getini('IMAGE'),
        config__salt_config=None,
        ssh_config={'user': 'root', 'password': 'admin123', 'port': 22})
    obj.run('zypper --non-interactive rm salt')  # Remove salt from the image!!

    request.addfinalizer(obj.remove)
    return obj


def test_ssh_option(master, sshdcontainer):
    '''
    Test test.ping working.
    '''

    master["container"]["config"]["salt_config"]["roster"].append(sshdcontainer)
    master.update_roster()

    master['container'].run("zypper --non-interactive in netcat-openbsd")
    SSH = (
        "salt-ssh -l quiet -i --out json --key-deploy --passwd admin123 "
        "--ssh-option='ProxyCommand=\"nc {0} 2222\"' {1} network.ip_addrs"
    ).format(sshdcontainer['ip'], sshdcontainer['config']['name'])
    return json.loads(str(master['container'].run(SSH).decode())).get('target') == sshdcontainer['ip']
