import pytest


pytestmark = pytest.mark.usefixtures("master", "minion", "minion_key_accepted")


def get_expectations(tags, oem=False):
    params = dict()

    if 'sles' in tags:
        params['productline'] = 'sles'
        params['release'] = 'OEM' if oem else '0'
    elif 'rhel' in tags:
        params['name'] = ''
        params['version'] = ''
        params['productline'] = ''
        params['release'] = ''

    if 'sles11sp3' in tags or 'sles11sp4' in tags:
        params['name'] = 'SUSE_SLES'
    elif 'sles12' in tags or 'sles12sp1' in tags:
        params['name'] = 'SLES'

    if 'sles11sp3' in tags:
        params['version'] = '11.3'
    elif 'sles11sp4' in tags:
        params['version'] = '11.4'
    elif 'sles12' in tags:
        params['version'] = '12'
    elif 'sles12sp1' in tags:
        params['version'] = '12.1'

    message = 'The config with this tags: {0} is not tested'.format(tags)
    assert not tags.isdisjoint({'sles', 'rhel'}), message
    assert not set(params).symmetric_difference(
        {'name', 'release', 'version', 'productline'}
    )

    return [['oem' if oem else 'nonoem'], params]


def pytest_generate_tests(metafunc):
    tags = set(metafunc.config.getini('TAGS'))
    metafunc.parametrize(
        'oem,expected',
        [get_expectations(tags), get_expectations(tags, oem=True)],
        ids=lambda it: ':'.join(it),
        indirect=['oem']
    )


@pytest.fixture()
def oem(request, minion):
    if request.param[0] == 'oem':
        suse_register = '/var/lib/suseRegister'
        with open('tests/oem.tar.gz', 'rb') as f:
            minion['container']['config']['docker_client'].put_archive(
                minion['container']['config']['name'], '/', f.read())
        request.addfinalizer(
            lambda: minion['container'].run('rm -rf {0}'.format(suse_register)))
    return request.param == 'oem'


@pytest.mark.xfailtags('rhel')
def test_pkg_list_products(minion, oem, expected):
    [output] = minion.salt_call('pkg.list_products')
    assert output['name'] == expected['name']
    assert output['version'] == expected['version']
    assert output['productline'] == expected['productline']
    assert output['release'] == expected['release']
