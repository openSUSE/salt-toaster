import pytest


pytestmark = pytest.mark.usefixtures("master", "minion")


def get_expectations(tags, oem=False):

    PARAMS = {
        'ubuntu1604': {
            'name': '',
            'version': '',
            'productline': '',
            'release': ''
        },
        'ubuntu1804': {
            'name': '',
            'version': '',
            'productline': '',
            'release': ''
        },
        'sles11sp3': {
            'name': 'SUSE_SLES',
            'version': '11.3',
            'productline': 'sles',
            'release': 'OEM' if oem else '1.201'
        },
        'sles11sp4': {
            'name': 'SUSE_SLES',
            'version': '11.4',
            'productline': 'sles',
            'release': 'OEM' if oem else '1.109'
        },
        'sles12': {
            'name': 'SLES',
            'version': '12',
            'productline': 'sles',
            'release': 'OEM' if oem else '0'
        },
        'sles12sp1': {
            'name': 'SLES',
            'version': '12.1',
            'productline': 'sles',
            'release': 'OEM' if oem else '0'
        },
        'sles12sp2': {
            'name': 'SLES',
            'version': '12.2',
            'productline': 'sles',
            'release': 'OEM' if oem else '0'
        },
        'sles12sp3': {
            'name': 'SLES',
            'version': '12.3',
            'productline': 'sles',
            'release': 'OEM' if oem else '0'
        },
        'sles15': {
            'name': 'SLES',
            'version': '15',
            'productline': 'sles',
            'release': 'OEM' if oem else '0'
        },
        'sles15sp1': {
            'name': 'SLES',
            'version': '15.1',
            'productline': 'sles',
            'release': 'OEM' if oem else '0'
        },
        'rhel': {
            'name': '',
            'version': '',
            'productline': '',
            'release': ''
        },
        'opensuse423': {
            'name': 'openSUSE',
            'version': '42.3',
            'productline': 'Leap',
            'release': '0'
        },
        'opensuse150': {
            'name': 'openSUSE',
            'version': '15.0',
            'productline': 'Leap',
            'release': '0'
        },
        'opensuse151': {
            'name': 'openSUSE',
            'version': '15.1',
            'productline': 'Leap',
            'release': '0'
        },
        'tumbleweed': {
            'name': 'openSUSE',
            'version': None, # Version changes on each snapshot
            'productline': 'openSUSE',
            'release': '0'
        },
        'opensuse': {
            'name': 'openSUSE',
            'version': '42.1',
            'productline': 'Leap',
            'release': '0'
        }
    }

    tag = set(tags).intersection(set(PARAMS)).pop()

    message = 'The config with this tags: {0} is not tested'.format(tags)
    assert not tags.isdisjoint({'sles', 'rhel', 'opensuse', 'ubuntu'}), message
    assert not set(PARAMS[tag]).symmetric_difference(
        {'name', 'release', 'version', 'productline'}
    )

    return [['oem' if oem else 'nonoem'], PARAMS[tag]]


def pytest_generate_tests(metafunc):
    tags = set(metafunc.config.getini('TAGS'))
    oem_params = get_expectations(tags, oem=True)
    non_oem_params = get_expectations(tags)
    metafunc.parametrize(
        'oem,expected',
        [non_oem_params, oem_params],
        ids=lambda it: ':'.join(it),
        indirect=['oem']
    )


@pytest.fixture()
def oem(request, minion):
    if request.param[0] == 'oem':
        with open('tests/oem.tar.gz', 'rb') as f:
            minion['container']['config']['client'].put_archive(
                minion['container']['config']['name'], '/', f.read())
        request.addfinalizer(
            lambda: minion['container'].run('rm -rf /var/lib/suseRegister'))
    return request.param == 'oem'


@pytest.mark.xfailtags('rhel', 'ubuntu')
def test_pkg_list_products(minion, oem, expected):
    [output] = minion.salt_call('pkg.list_products')
    assert output['name'] == expected['name']
    if 'Tumbleweed' not in output['summary']:
        assert output['version'] == expected['version']
    assert output['productline'] == expected['productline']
    assert output['release'] == expected['release']
