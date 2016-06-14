import pytest


pytestmark = pytest.mark.usefixtures("master", "minion", "minion_key_accepted")


INSTALLED = [
    'salt-minion',
    'salt-proxy',
    'salt',
    'salt-master',
    'salt-cp',
    'salt-key',
    'salt-run',
    'spm',
    'salt-call',
    'salt-unity',
]


MISSING = [
    'salt-api',
    'salt-cloud',
    'salt-ssh',
    'salt-syndic',
]


@pytest.mark.parametrize("component", INSTALLED)
def tests_component_installed(master, minion, component):
    output = minion['container'].run([component, '--version'])
    assert 'executable file not found' not in output


@pytest.mark.parametrize("component", MISSING)
@pytest.mark.xfail
def tests_component_installed_missing(minion, component):
    output = minion['container'].run([component, '--version'])
    assert 'executable file not found' in output
