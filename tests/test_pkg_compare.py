import json
import pytest


pytestmark = pytest.mark.usefixtures("master", "minion")


def pytest_generate_tests(metafunc):
    tags = set(metafunc.config.getini('TAGS'))
    VERSIONS = [
        ['0.2-1', '0.2-1', 0],
        ['0.2-1.0', '0.2-1', 1],
        ['0.2.0-1', '0.2-1', 1],
        ['0.2-1', '1:0.2-1', -1],
        ['1:0.2-1', '0.2-1', 1],
    ]
    if not tags.isdisjoint(
        {'sles15', 'sles12', 'sles12sp1', 'sles12sp2', 'leap42sp1', 'rhel6', 'rhel7'}
    ):
        VERSIONS += [
            ['0.2-1', '0.2~beta1-1', 1],
            ['0.2~beta2-1', '0.2-1', -1]
        ]
    else:
        VERSIONS += [
            ['0.2-1', '0.2~beta1-1', -1],
            ['0.2~beta2-1', '0.2-1', 1]
        ]
    metafunc.parametrize(
        "params", VERSIONS, ids=lambda it: '{0}:{1}:{2}'.format(*it))


def test_pkg_compare(params, minion):
    [ver1, ver2, expected] = params
    command = "salt-call pkg.version_cmp {0} {1} --output=json -l quiet".format(
        ver1, ver2
    )
    raw = minion['container'].run(command)
    assert json.loads(raw)['local'] == expected
