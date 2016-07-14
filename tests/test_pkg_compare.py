import json
import pytest


pytestmark = pytest.mark.usefixtures(
    "platform_required", "master", "minion", "minion_key_accepted")


PRE_SLE12 = [
    ['0.2-1', '0.2~beta1-1', '-1'],
    ['0.2~beta2-1', '0.2-1', '1']
]


POST_SLE12 = [
    ['0.2-1', '0.2~beta1-1', '1'],
    ['0.2~beta2-1', '0.2-1', '-1']
]


def pytest_generate_tests(metafunc):
    VERSIONS = [
        ['0.2-1', '0.2-1', '0'],
        ['0.2-1.0', '0.2-1', '1'],
        ['0.2.0-1', '0.2-1', '1'],
        ['0.2-1', '1:0.2-1', '-1'],
        ['1:0.2-1', '0.2-1', '1'],
    ] + PRE_SLE12 + POST_SLE12
    metafunc.parametrize("params", VERSIONS)


def check_params(major, params):
    if (
        (major >= 12 and params in PRE_SLE12) or
        (major < 12 and params in POST_SLE12)
    ):
        pytest.skip("not for this version")


@pytest.mark.platform('sles')
def test_pkg_compare(params, minion):
    info = minion['container'].get_suse_release()
    major, minor = info['VERSION'], info['PATCHLEVEL']

    check_params(major, params)

    [ver1, ver2, expected] = params

    command = "salt-call pkg.version_cmp {0} --output=json -l quiet".format(
        ' '.join([ver1, ver2])
    )
    raw = minion['container'].run(command)
    assert json.loads(raw)['local'] == int(expected)
