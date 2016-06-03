import pytest
from utils import get_suse_release


pytestmark = pytest.mark.usefixtures("master", "minion_ready")


def pytest_generate_tests(metafunc):
    VERSIONS = [
        ['0.2-1', '0.2-1', '0'],
        ['0.2-1.0', '0.2-1', '1'],
        ['0.2.0-1', '0.2-1', '1'],
        ['0.2-1', '1:0.2-1', '-1'],
        ['1:0.2-1', '0.2-1', '1']
    ]

    PRE_SLE12 = [
        ['0.2-1', '0.2~beta1-1', '-1'],
        ['0.2~beta2-1', '0.2-1', '1']
    ]

    POST_SLE12 = [
        ['0.2-1', '0.2~beta1-1', '1'],
        ['0.2~beta2-1', '0.2-1', '-1']
    ]
    info = get_suse_release()
    major, minor = info['VERSION'], info['PATCHLEVEL']
    metafunc.parametrize(
        "ver1,ver2,expected",
        VERSIONS + POST_SLE12 if major >= 12 else VERSIONS + PRE_SLE12
    )

def test_pkg_compare(ver1, ver2, expected, caller_client):
    assert caller_client.cmd('pkg.version_cmp', ver1, ver2) == int(expected)
