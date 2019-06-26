import pytest
from .common import GRAINS_EXPECTATIONS


pytestmark = pytest.mark.usefixtures("master")



def pytest_generate_tests(metafunc):
    functions = [
        'test_get_osarch',
        'test_get_os',
        'test_get_oscodename',
        'test_get_os_family',
        'test_get_osfullname',
        'test_get_osrelease',
        'test_get_osrelease_info'
    ]
    expectations = GRAINS_EXPECTATIONS
    tags = set(metafunc.config.getini('TAGS'))
    tag = set(tags).intersection(set(expectations)).pop()
    if metafunc.function.__name__ in functions and tag:
        metafunc.parametrize(
            'expected', [expectations[tag]], ids=lambda it: tag)


def test_get_cpuarch(minion):
    assert minion.salt_call('grains.get', 'cpuarch') == 'x86_64'


def test_get_os(minion, expected):
    key = 'os'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_items(minion):
    assert minion.salt_call('grains.get', 'items') == ''


def test_get_os_family(minion, expected):
    key = 'os_family'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_oscodename(minion, expected):
    key = 'oscodename'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_osfullname(minion, expected):
    key = 'osfullname'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_osarch(minion, expected):
    assert minion.salt_call('grains.get', 'osarch') == expected.get('osarch', 'x86_64')


def test_get_osrelease(minion, expected):
    key = 'osrelease'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_osrelease_info(minion, expected):
    key = 'osrelease_info'
    assert minion.salt_call('grains.get', 'osrelease_info') == expected[key]

@pytest.mark.skiptags('products-next', 'ubuntu')
def test_salt_version(minion):
    rpm_version = minion['container'].run('rpm -q salt --queryformat "%{VERSION}"')
    assert minion.salt_call('grains.get', 'saltversion') == rpm_version
