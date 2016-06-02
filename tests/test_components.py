import pytest
import subprocess

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
def tests_component_installed(component):
    try:
        process = subprocess.Popen(
            [component, '--version'], stdout=subprocess.PIPE, env={})
        assert process.returncode is None
    except OSError:
        raise Exception('{0} not installed.'.format(component))


@pytest.mark.parametrize("component", MISSING)
@pytest.mark.xfail
def tests_component_installed_missing(component):
    try:
        process = subprocess.Popen(
            [component, '--version'], stdout=subprocess.PIPE, env={})
        assert process.returncode is None
    except OSError:
        raise Exception('{0} not installed.'.format(component))
