import pytest


pytestmark = pytest.mark.usefixtures("master", "minion", "minion_key_accepted")


def get_expectations(tags, oem=False):

    PARAMS = {
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
        'rhel': {
            'name': '',
            'version': '',
            'productline': '',
            'release': ''
        }
    }

    tag = set(tags).intersection(set(PARAMS)).pop()

    message = 'The config with this tags: {0} is not tested'.format(tags)
    assert not tags.isdisjoint({'sles', 'rhel'}), message
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
            minion['container']['config']['docker_client'].put_archive(
                minion['container']['config']['name'], '/', f.read())
        request.addfinalizer(
            lambda: minion['container'].run('rm -rf /var/lib/suseRegister'))
    return request.param == 'oem'


@pytest.mark.xfailtags('rhel')
def test_pkg_list_products(minion, oem, expected):
    [output] = minion.salt_call('pkg.list_products')
    assert output['name'] == expected['name']
    assert output['version'] == expected['version']
    assert output['productline'] == expected['productline']
    assert output['release'] == expected['release']
