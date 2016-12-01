import pytest


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
    expectations = {
        'rhel6': {
            'os': 'RedHat',
            'oscodename': 'Santiago',
            'os_family': 'RedHat',
            'osfullname': 'Red Hat Enterprise Linux Server',
            'osrelease': '6.8',
            'osrelease_info': [6, 8],
        },
        'rhel7': {
            'os': 'RedHat',
            'oscodename': 'Red Hat Enterprise Linux Server 7.2 (Maipo)',
            'os_family': 'RedHat',
            'osfullname': 'Red Hat Enterprise Linux Server',
            'osrelease': '7.2',
            'osrelease_info': [7, 2],
        },
        'sles11sp3': {
            'os': 'SUSE',
            'oscodename': 'SUSE Linux Enterprise Server 11 SP3',
            'os_family': 'Suse',
            'osfullname': 'SLES',
            'osrelease': '11.3',
            'osrelease_info': [11, 3],
        },
        'sles11sp4': {
            'os': 'SUSE',
            'oscodename': 'SUSE Linux Enterprise Server 11 SP4',
            'os_family': 'Suse',
            'osfullname': 'SLES',
            'osrelease': '11.4',
            'osrelease_info': [11, 4],
        },
        'sles12': {
            'os': 'SUSE',
            'oscodename': 'SUSE Linux Enterprise Server 12',
            'os_family': 'Suse',
            'osfullname': 'SLES',
            'osrelease': '12',
            'osrelease_info': [12],
        },
        'sles12sp1': {
            'os': 'SUSE',
            'oscodename': 'SUSE Linux Enterprise Server 12 SP1',
            'os_family': 'Suse',
            'osfullname': 'SLES',
            'osrelease': '12.1',
            'osrelease_info': [12, 1],
        },
        'leap42sp1': {
            'os': 'openSUSE Leap',
            'oscodename': 'openSUSE Leap 42.1 (x86_64)',
            'os_family': 'Suse',
            'osfullname': 'openSUSE Leap',
            'osrelease': '42.1',
            'osrelease_info': [42, 1],
        }
    }
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
