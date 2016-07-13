import pytest


pytestmark = pytest.mark.usefixtures("master_container")


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
def tests_component_installed(master_container, component):
    output = master_container.run([component, '--version'])
    assert 'executable file not found' not in output


@pytest.mark.parametrize("component", MISSING)
def tests_component_installed_missing(master_container, component):
    output = master_container.run([component, '--version'])
    assert 'executable file not found' in output
