import pytest
from tests.common import GRAINS_EXPECTATIONS


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


@pytest.mark.tags('rhel', 'fedora')
def test_ssh_pkg_info_rhel(master):
    '''
    Test pkg.info_instaled on RHEL series
    '''
    assert master.salt_ssh("pkg.info_installed python").get('python', {}).get('install_date')


@pytest.mark.tags('sles', 'leap')
def test_ssh_pkg_info_sles(master):
    '''
    Test pkg.info_installed on SLES series
    '''
    assert master.salt_ssh("pkg.info_installed python").get('python', {}).get('installed')


def test_ssh_pkg_install(master):
    '''
    Test pkg.install
    '''
    master.salt_ssh("cmd.run 'zypper --non-interactive rm test-package'")
    out = master.salt_ssh("pkg.install test-package")
    import pdb;pdb.set_trace()
    #assert bool(out.get('test-package', {}).get('new'))
    #assert not bool(out.get('test-package', {}).get('old'))


def test_ssh_pkg_remove(master):
    '''
    Test pkg.remove
    '''
    master.salt_ssh("cmd.run 'zypper --non-interactive in test-package'")
    out = master.salt_ssh("pkg.remove test-package")
    assert bool(out.get('test-package', {}).get('old'))
    assert not bool(out.get('test-package', {}).get('new'))
