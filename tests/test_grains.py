import pytest
from common import GRAINS_EXPECTATIONS


pytestmark = pytest.mark.usefixtures("master")



def pytest_generate_tests(metafunc):
    functions = [
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
    if metafunc.function.func_name in functions and tag:
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
    # Do not test "2015.8.7 (Beryllium)"
    if '2015.8.7' in minion.salt_call('cmd.run', '"salt --version"'):
        return

    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_osfullname(minion, expected):
    key = 'osfullname'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_osarch(minion):
    assert minion.salt_call('grains.get', 'osarch') == 'x86_64'


def test_get_osrelease(minion, expected):
    key = 'osrelease'
    assert minion.salt_call('grains.get', key) == expected[key]


def test_get_osrelease_info(minion, expected):
    key = 'osrelease_info'
    assert minion.salt_call('grains.get', 'osrelease_info') == expected[key]
